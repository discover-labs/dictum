# Types and Formatting

When it comes to generating queries on the backend, Hyperplane is naive about data types.
It will let you subtract a date from a number if you write such an expression, and it
will fail at query time.

At the same time, each calculation has a type. Type information allows Hyperplane to
achieve two things:

- Establish expectations about which Python types will be returned from the backend.
- Correcly format query output.

Formatting, e.g. turning `1234.4` into `$1,234.40`, is done on the server. A client can
request the data in the formatted form (then all values are strings) or without formatting — 
then all values are just the type they are, with the exception of `date` and `datetime`,
which are represented as ISO-compliant strings.

Types establish "baseline" formatting with sane defaults, which can be further tuned
with `format` calculation field.

!!! important
    Formatting only affects how the values are displayed, not how they're calculated.
    If you group some metric by a date dimension and format the date as just a year (`%Y`),
    the resulting table will have as many rows as you have unique _dates_ in your table.


## Project locale

Locale is defined by the `locale` setting at the root of the project. The default locale
is `en_US`.

!!! info
    Server-side locale-aware formatting is provided by
    [Babel](http://babel.pocoo.org/en/latest/index.html) library.


## Numeric types

Numeric types are `number`, `decimal`, `percent` and `currency`. `number` and `decimal`
mainly do the same thing: format your value as a number.

`percent` will format your values as a percentage: it will be multiplied by 100 and appended
with a `%` symbol. Rounding is defined by the locale.

`currency` will give you a string formatted as a money value, like the example above:
`1234.4` will be shown as `$1,234.40`. If a calculation's type is `currency`, then
you have to provide a 3-letter currency code:

```yaml
measures:
  money:
    name: Money (Rubles)
    expr: sum(money_rub)
    type: currency
    currency: RUB
```

### Numeric type format patterns

!!! tip
    For Babel documentation on pattern syntax, see
    [here](http://babel.pocoo.org/en/latest/numbers.html#pattern-syntax).

Pattern syntax for customizing number format might be familiar to you: it's similar to
the ones used in Excel and Tableau.

| Symbol                        | Description                                      |
|-------------------------------|--------------------------------------------------|
| `0`                           | Digit, absent shown as `0`                       |
| `#`                           | Digit, zero shown as absent                      |
| `@`                           | Significant digit                                |
| `.`                           | Decimal separator or monetary decimal separator. |
| `,`                           | Grouping separator                               |
| `-`                           | Minus sign                                       |
| `+`                           | Prefix positive numbers with a plus sign         |
| `;`                           | Separates positive and negative subpatterns      |
| `%`                           | Multiply by 100 and show as percentage           |
| `‰`                           | Multiply by 1000 and show as per mille           |
| `E`                           | Separates mantissa and exponent in scientific notation |
| `¤`                           | Currency sign, replaced by currency symbol. If doubled, replaced by international currency symbol. If tripled, uses the long form of the decimal symbol. |
| `'`                           | Used to quote special characters in a prefix or suffix |
| `*`                           | Pad escape, precedes pad character               |

This is a lot, so to clarify a little bit, let's go through some examples.

If you store a year as an `integer`, and want to avoid it being displayed as `2,021`,
use `format: "####"`. The default format in most locales uses a grouping separator for
each three positions: `#,###`.

If you want to have exactly two positions after a floating point, use this format:
`#.00`. This will show `.00` at the end even if there is nothing there in the value.
So, `3` becomes `3.00` with this format, and PI (`3.141592653589793`) becomes
`3.14`.

The `0` character works both ways. If you want to have _at least_ four digits before
the decimal separator, do this: `0000`. If your number is shorter than four digits, it
will be padded by zeros: `23` will be `0023`, but `23456` will stay `23456`.

If you just want to do rounding (without zero padding), use `#`. `0.##` will round the
numbers to two digits after the separator: PI will be `3.14`, but `3` will be just `3`.

Positive and negative subpatterns work like the following: the first part before `;`
is a format for positive numbers, the next is for negative. If you want to use finance
notation for losses, use this format: `0.00;(0.00)`. `500` will be shown as `500.00`,
but `-500` as `(500.00)`.

Significant digits (`@`) allow you to make non-fractional numbers rounded to any number
of significant positions. `@@` will turn `1234` into `1200`, `1654` into `1700`.

Percentages work the same way as normal numbers, but you have to add `%` at the end
of the format pattern. `#.###%` will turn `0.141592` into `14.159%`.

The `¤` symbol means a currency. Let's take `JPY` (Japanese yen) and value `1234` as an
example.

- `¤#,###` format will give you `¥1,234` (in `en_US` locale)
- `#,### ¤¤` will give `1,234 JPY`
- `#,### ¤¤¤` — `1,234 Japanese yen`


## `date` and `datetime` types

!!! important
