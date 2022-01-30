```yaml
type: root | table | metric | dimension | union | domain | profile
domain: ID

# root
name: str
description: str
tables: id -> table
metrics: id -> metric
dimensions: id -> dimension
unions: id -> union
domains: id -> domain
profiles: id -> profile

# table
id: str  # if not k:v
primary_key: str
related:
    ID:
        table: ID
        foreign_key: str
        related_key: str
measures: id -> metric
dimensions: id -> dimension
filters: List[Expr]


domain: str

domains:
    ID:
        name: str
        description: str
        owner: str

tables:
    ID:
        source: str | dict
        primary_key: str
        related:
            ID:
                table: ID
                foreign_key: str
                related_key: Optional[str]
        measures:
            ID:
                ...  # calculation stuff
        dimensions:
            ID:
                name: str
                expr: str
                type: Literal["int", "float", "str", "date", "datetime", "bool"]

metrics:
    ID:
        name: str
        expr: str
        table: Optional[str]
        description: Optional[str]

dimensions:
    ID:
        name: str
        expr: str
        table: Optional[str]
        description: Optional[str]

unions:
    ID:
        name: ...
        description: ...
        type: ...

profiles:
    ID:
        type: str  # sqlite | postgres
        params: dict

default_profile: ID
```

```yaml
module: main

tables:
    invoice_items:
        source: invoice_items
        related:
            invoice: [Invoices, InvoiceId]
            track: [tracks, TrackId]
    invoices:
        source: invoices
        primary_key: InvoiceId
    tracks:
        source: tracks
        related:
            album:
                table: albums
                foreign_key: AlbumId
            artist:
                table: artists
                foreign_key: ArtistId
            genre:
                table: genres
                foreign_key: GenreId
    albums:
        source: albums
        primary_key: AlbumId
    genres:
        source: genres
        primary_key: GenreId
    artists:
        source: artists
        primary_key: ArtistId

metrics:
    revenue:
        name: Revenue
        expr: sum(UnitPrice * Quantity)
        table: invoice_items
        type: float
        format: USD
        missing: 0
    revenue_per_track:
        name: Revenue per Track
        expr: $revenue / $tracks

dimensions:
    date:
        table: invoices
        name: Sale Date
        expr: InvoiceDate
        type: datetime
```
