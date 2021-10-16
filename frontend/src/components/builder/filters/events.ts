interface Events {
    type: string;
}

export interface CheckboxToggleEvent extends Event {
    detail: { label: string }
}

export interface ValuesFilterToggleEvent extends CheckboxToggleEvent {
    detail: { label: string, id: string }
}
