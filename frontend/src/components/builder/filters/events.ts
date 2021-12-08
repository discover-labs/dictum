interface Events {
    type: str;
}

export interface CheckboxToggleEvent extends Event {
    detail: { label: string }
}

export interface ValuesFilterToggleEvent extends CheckboxToggleEvent {
    detail: { label: string, id: string }
}
