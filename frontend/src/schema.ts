import type { FormatLocaleDefinition } from "d3-format";
import type { TimeLocaleDefinition } from "d3-time-format";

export interface Store {
    measures: Measure[];
    dimensions: Dimension[];
}

type CalculationType = "time" | "continuous" | "ordinal" | "nominal";

export interface Calculation {
    id: string;
    name: string;
    description: string | null;
    type: CalculationType;
    format: CalculationFormat;
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

export interface CalculationFormat {
    spec: string;
    currencyPrefix: string;
    currencySuffix: string;
}

interface LocaleDefinition {
    number: FormatLocaleDefinition;
    time: TimeLocaleDefinition;
}

export interface QueryResultMetadata {
    columns: Calculation[];
    store: Store;
    locale: LocaleDefinition;
}
