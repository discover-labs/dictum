export interface Store {
    measures: Measure[];
    dimensions: Dimension[];
}

type CalculationType = "number" | "decimal" | "percent" | "currency" | "date" | "datetime" | "string";

export interface Calculation {
    id: string;
    name: string;
    description: string | null;
    type: CalculationType;
    format: String;
    currency: String | null;
}

export interface Measure extends Calculation { }
export interface Metric extends Calculation {
    dimensions: Dimension[];
}


export interface Dimension extends Calculation {
}

export interface DimensionInfo {
    dimension: Dimension;
    range: [number, number] | null;
    values: any[] | null;
}

export interface Query {
    measures: Array<string>;
    dimensions: Array<string>;
    filters?: Array<string>;
}


export interface QueryResult {
    query: Query;
    data: object[];
    metadata: QueryResultMetadata;
}

export interface QueryResultMetadata {
    rawQuery: string;
    columns: Calculation[];
    store: Store;
    locale: String;
}
