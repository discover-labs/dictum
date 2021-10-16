import type { FormatLocaleDefinition } from "d3-format";
import type { TimeLocaleDefinition } from "d3-time-format";

export interface Store {
    measures: Measure[];
    dimensions: Dimension[];
}

export interface Calculation {
    id: string;
    name: string;
    description: string | null;
}


export interface Measure extends Calculation { }


type DimensionType = "time" | "continuous" | "ordinal" | "nominal";


export interface Dimension extends Calculation {
    type: DimensionType;
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

type CalculationKind = "measure" | "dimension";

export interface CalculationFormat {
    spec: string;
    currency_prefix: string;
    currency_suffix: string;
}

interface CalculationMetadata {
    name: string;
    kind: CalculationKind;
    type?: DimensionType;
    format: CalculationFormat;
}

interface LocaleDefinition {
    number: FormatLocaleDefinition;
    time: TimeLocaleDefinition;
}

export interface QueryResultMetadata {
    columns: { [key: string]: CalculationMetadata };
    store: Store;
    locale: LocaleDefinition;
}
