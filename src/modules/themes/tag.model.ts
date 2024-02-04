export interface ITag {
    id: string;
    active: boolean;
    themes: string[];
    children?: ITag[];
    elements: {
        mobile?: HTMLInputElement,
        desktop?: HTMLInputElement
    };
    parentRef?: ITag;
}
