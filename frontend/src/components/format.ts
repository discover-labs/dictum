import { formatLocale } from "d3-format";
import { timeFormatLocale } from "d3-time-format";
import type { QueryResultMetadata, CalculationFormat, Calculation } from "../schema";
import type { FormatLocaleDefinition } from "d3-format";
import type { TimeLocaleDefinition } from "d3-time-format";


const identity = (x: any) => x

function getFormatter(defn: FormatLocaleDefinition, format?: CalculationFormat | null) {
    if (typeof (format) === "undefined" || format === null) {
        return identity
    }
    const currency = (format.currencyPrefix.length > 0 || format.currencySuffix.length > 0) ? [format.currencyPrefix, format.currencySuffix] :
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
    const { time, number } = metadata.locale;
    return metadata.columns.reduce((prev, curr) =>
        Object.assign(prev, {
            [curr.id]: curr.type === "time"
                ? getTimeFormatter(time, curr.format)
                : getFormatter(number, curr.format)
        }), {});
}
