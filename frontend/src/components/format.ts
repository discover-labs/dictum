import { formatLocale } from "d3-format";
import { timeFormatLocale } from "d3-time-format";
import type { QueryResultMetadata, CalculationFormat } from "../schema";
import type { FormatLocaleDefinition } from "d3-format";
import type { TimeLocaleDefinition } from "d3-time-format";


const identity = (x: any) => x

function getFormatter(defn: FormatLocaleDefinition, format?: CalculationFormat | null) {
    if (typeof (format) === "undefined" || format === null) {
        return identity
    }
    const currency = (format.currency_prefix.length > 0 || format.currency_suffix.length > 0) ? [format.currency_prefix, format.currency_suffix] :
        defn.currency;
    const currencyLocale = Object.assign({}, defn, { currency: currency })
    const locale = formatLocale(currencyLocale);
    return locale.format(format.spec);
}

function getTimeFormatter(defn: TimeLocaleDefinition, format?: CalculationFormat | null) {
    if (typeof (format) === "undefined" || format === null) {
        return identity
    }
    const locale = timeFormatLocale(defn);
    const formatter = locale.format(format.spec);
    return (val: any): string => {
        const parsed = new Date(val);
        return formatter(parsed);
    }
}

export function getFormatters(metadata: QueryResultMetadata) {
    let result = {};
    Object.keys(metadata.columns).forEach((k) => {
        const col = metadata.columns[k];
        if (col.type === "time") {
            result[k] = getTimeFormatter(metadata.locale.time, col.format);
        } else {
            result[k] = getFormatter(metadata.locale.number, col.format);
        }
    })
    return result;
}
