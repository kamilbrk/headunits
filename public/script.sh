#!/bin/bash

# OTA Processing Script
# Tested on macOS and Linux
# Ensure the script is executable: chmod +x script.sh

# Installation and usage (macOS Sonoma with Apple Silicon)

# 2. Then you can use pre-compiled tools in the supplied "bin" folder, although if you feel like getting all that stuff yourself or perhaps updating the binaries:
#     - Create "bin" folder next to this script
#     - Build ext4fuse from source:
#         ```sh
#         git clone https://github.com/gerard/ext4fuse.git
#         cd ext4fuse
#         make
#         ```
#         and put that entire ext4fuse folder into "bin"
#     - Get payload-dumper-go from https://github.com/ssut/payload-dumper-go and make it executable
#         ```sh
#         chmod +x payload-dumper-go
#         ```
#         and similarly, put that into the "bin" folder
#     - Get sdat2img.py file from https://github.com/xpirt/sdat2img and put that into "bin" folder as well

# 3. Install tools using Homebrew on macOS
#     ```sh
#     brew install brotli # only needed for Android 10 images
#     brew install apktool
#     brew install jadx
#     ```

# 4. Make sure the provided script is executable:
#     ```sh
#     chmod +x script.sh
#     ```

# 5. Download KSW OTA zip updates

# 6. Run it like so
#     ```sh
#     ./script.sh ./Firmwares/Ksw-T-M600_OS_v1.6.5-ota.zip --frontmatter --decompile-apk --decompile-jar
#     ```

# Global Variables
DECOMPILE_APK=false
DECOMPILE_JAR=false
GENERATE_FRONTMATTER=false
OTA_FILE=""
STANDARD_USER=$(whoami)

# Function to parse arguments
parse_args() {
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --decompile-apk) DECOMPILE_APK=true ;;
      --decompile-jar) DECOMPILE_JAR=true ;;
      --frontmatter) GENERATE_FRONTMATTER=true ;;
      -*|--*=) echo "Error: Unsupported flag $1" >&2; exit 1 ;;
      *) OTA_FILE="$1" ;;
    esac
    shift
  done

  if [[ -z "$OTA_FILE" ]]; then
    echo "Error: OTA file path is required."
    exit 1
  fi
}

# Function to check and acquire sudo permissions
check_sudo() {
  if [[ $UID -ne 0 ]]; then
    echo "Enter sudo password once to avoid interruptions."
    sudo -v
  fi
}

# Function to initialize paths
initialize_paths() {
  FULLPATH="$OTA_FILE"
  FILENAME="${FULLPATH##*/}"
  DIR="${FULLPATH%/*}"
  BASE="${FILENAME%.*}"
  EXT="${FILENAME##*.}"

  UNCOMPRESSED_DIR="$DIR/$BASE/uncompressed"
  PARTITIONS_DIR="$DIR/$BASE/partitions"
  OUTPUT_DIR="$DIR/$BASE/output"
}

# Function to unzip OTA file
unzip_ota() {
  echo " - Unzipping OTA file"
  unzip -qq "$FULLPATH" -d "$UNCOMPRESSED_DIR"
}

# Function to handle DAT partitions from brotli
get_dat_from_brotli() {
  for image in 'system' 'vendor'; do
    local br_file="$UNCOMPRESSED_DIR/$image.new.dat.br"
    local dat_file="$UNCOMPRESSED_DIR/$image.new.dat"
    if [[ -f "$br_file" && ! -f "$dat_file" ]]; then
      echo " - Decompressing $image image"
      brotli --decompress --output="$dat_file" "$br_file"
    fi
  done
}

# Function to convert DAT to IMG
get_images_from_dat() {
  for image in 'system' 'vendor'; do
    local transfer_list="$UNCOMPRESSED_DIR/$image.transfer.list"
    local dat_file="$UNCOMPRESSED_DIR/$image.new.dat"
    local img_file="$PARTITIONS_DIR/$image.img"
    if [[ -f "$transfer_list" && -f "$dat_file" && ! -f "$img_file" ]]; then
      echo " - Converting $image image"
      python ./bin/sdat2img.py "$transfer_list" "$dat_file" "$img_file"
    fi
  done
}

# Function to extract IMG from BIN
get_images_from_bin() {
  local payload_file="$UNCOMPRESSED_DIR/payload.bin"
  if [[ -f "$payload_file" ]]; then
    echo " - Extracting partitions from payload.bin"
    ./bin/payload-dumper-go -c 4 -o "$PARTITIONS_DIR" "$payload_file"
  fi
}

# Function to mount and copy from partitions
mount_and_copy_from_partitions() {
  for image in 'system' 'odm' 'product' 'system_dlkm' 'system_ext' 'vendor' 'vendor_dlkm'; do
    local img_file="$PARTITIONS_DIR/$image.img"
    local mount_point="$PARTITIONS_DIR/$image"
    if [[ -f "$img_file" ]]; then
      echo " - Processing partition $image"
      mkdir -p "$mount_point"
      sudo ./bin/ext4fuse/ext4fuse "$img_file" "$mount_point" -o allow_other,defer_permissions

      if [[ $? -eq 0 ]]; then
        if [[ "$image" == "system" ]]; then
          echo "   - Copying main system files"
          sudo cp -R "$mount_point/system/" "$OUTPUT_DIR/"
        else
          echo "   - Copying $image files"
          sudo rm -rf "$OUTPUT_DIR/$image"
          sudo cp -R "$mount_point" "$OUTPUT_DIR/$image"
        fi
        sudo umount "$mount_point"
      fi
      rm -rf "$mount_point"
    fi
  done
}

# Function to convert Unix time to ISO 8601 format
convert_unix_to_iso() {
  local unix_time="$1"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    date -u -r "$unix_time" +"%Y-%m-%dT%H:%M:%SZ"
  else
    date -u -d @"$unix_time" +"%Y-%m-%dT%H:%M:%SZ"
  fi
}

# Function to get property value from a file
get_prop_value() {
  local file_path="$1"
  local property_name="$2"
  local property_value=""

  # Check if the file exists
  if [ ! -f "$file_path" ]; then
    echo "Error: $file_path not found!"
    return 1
  fi

  # Read through the file to find the specified property
  while IFS= read -r line; do
    if [[ "$line" == *"$property_name="* ]]; then
      # Extract the value after the equal sign
      property_value="${line#*=}"
      break
    fi
  done < "$file_path"

  # Check if the variable is set
  if [ -z "$property_value" ]; then
    echo ""
    return 0
  fi

  # Return the property value
  echo "$property_value"
  return 0
}

# Function to generate file signatures
generate_signature() {
  local file="$1"
  local algorithm="$2"

  if [[ "$algorithm" == "md5" ]]; then
    if command -v md5sum >/dev/null 2>&1; then
      md5sum "$file" | awk '{ print $1 }'
    elif command -v md5 >/dev/null 2>&1; then
      md5 -q "$file"
    else
      echo "command not found"
    fi
  elif [[ "$algorithm" == "sha1" ]]; then
    if command -v sha1sum >/dev/null 2>&1; then
      sha1sum "$file" | awk '{ print $1 }'
    elif command -v shasum >/dev/null 2>&1; then
      shasum -a 1 "$file" | awk '{ print $1 }'
    else
      echo "command not found"
    fi
  elif [[ "$algorithm" == "sha256" ]]; then
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum "$file" | awk '{ print $1 }'
    elif command -v shasum >/dev/null 2>&1; then
      shasum -a 256 "$file" | awk '{ print $1 }'
    else
      echo "command not found"
    fi
  else
    echo "unsupported algorithm"
  fi
}

# Function to determine vendor and platform from the string
determine_vendor_platform() {
  local input_string="$1"
  local vendor=""
  local platform=""

  if [[ "$input_string" == GT* ]]; then
    vendor="zxw"
    if [[ "$input_string" == GT6* ]]; then
      platform="gt6"
    elif [[ "$input_string" == GT7* ]]; then
      platform="gt7"
    fi
  elif [[ "$input_string" == Ksw* ]]; then
    vendor="ksw"
    if [[ "$input_string" == *-M700* ]]; then
      platform="m700"
    elif [[ "$input_string" == *-M600* ]]; then
      platform="m600"
    elif [[ "$input_string" == *-Userdebug* ]]; then
      platform="m501"
    fi
  fi

  echo "$vendor $platform"
}

# Function to generate frontmatter
generate_frontmatter() {
  local id="$BASE"

  # Vendor and platform
  local display_id_root=$(get_prop_value "$OUTPUT_DIR/build.prop" "ro.build.display.id")
  local display_id_vendor=$(get_prop_value "$OUTPUT_DIR/vendor/build.prop" "ro.build.display.id")
  local display_id="${display_id_root:-$display_id_vendor}"
  local vendor_platform=$(determine_vendor_platform "$display_id")
  read vendor platform <<< "$vendor_platform"

  local android=$(get_prop_value "$OUTPUT_DIR/build.prop" "ro.system.build.version.release")
  local date_unix=$(get_prop_value "$OUTPUT_DIR/build.prop" "build.date.utc")
  local date_iso=$(convert_unix_to_iso "$date_unix")

  echo "---"
  echo "id: \"$id\""
  echo "vendor: $vendor"
  echo "platform: $platform"
  echo "android: $android"
  echo "date: $date_iso"
  echo "signatures:"
  local signature_md5=$(generate_signature "$FULLPATH" md5)
  echo "  md5: $signature_md5"
  local signature_sha1=$(generate_signature "$FULLPATH" sha1)
  echo "  sha1: $signature_sha1"
  local signature_sha256=$(generate_signature "$FULLPATH" sha256)
  echo "  sha256: $signature_sha256"
  echo "---"
}

# Function to handle main processing flow
main_flow() {
  echo " - Creating directories"
  mkdir -p "$OUTPUT_DIR" "$PARTITIONS_DIR" "$UNCOMPRESSED_DIR"

  unzip_ota
  get_dat_from_brotli
  get_images_from_dat
  get_images_from_bin

  echo " - Cleaning up uncompressed files"
  rm -rf "$UNCOMPRESSED_DIR"

  mount_and_copy_from_partitions

  echo " - Cleaning up partitions"
  rm -rf "$PARTITIONS_DIR"

  echo " - Fixing permissions"
  sudo chown -R "$STANDARD_USER" "$OUTPUT_DIR/"

  echo " - All files have been extracted"
}

# Function to decompile APKs using JADX
decompile_apks() {
  find "$OUTPUT_DIR" -type f -name "*.apk" -print0 | while IFS= read -r -d '' apk_file; do
    sudo jadx -q --no-debug-info --comments-level none -m restructure -e "$apk_file" -d "${apk_file}.out"
  done
}

# Function to decompile JARs using APKTOOL
decompile_jars() {
  find "$OUTPUT_DIR" -type f -name "*.jar" -print0 | while IFS= read -r -d '' jar_file; do
    sudo apktool d -q -b -o "${jar_file}.out" "$jar_file"
  done
}

# Function to open Meld to see diffs between two folders
# Not used yet.
open_meld() {
  local folder1="$1"
  local folder2="$2"
  open -W -a Meld --args "$folder1" "$folder2"
}

# Main script execution
parse_args "$@"
check_sudo
initialize_paths

if [[ ! -d "$OUTPUT_DIR/vendor/bin" ]]; then
  main_flow
else
  echo " - Files already extracted"
fi

if [[ "$GENERATE_FRONTMATTER" == true ]]; then
  echo " - Generating Frontmatter metadata"
  generate_frontmatter
fi

if [[ "$DECOMPILE_JAR" == true ]]; then
  echo " - Decompiling JAR files"
  decompile_jars
  echo " - Finished decompiling JAR files"
else
  echo " - Skipping JAR decompilation"
fi

if [[ "$DECOMPILE_APK" == true ]]; then
  echo " - Decompiling APK files"
  decompile_apks
  echo " - Finished decompiling APK files"
else
  echo " - Skipping APK decompilation"
fi

echo "All done"
