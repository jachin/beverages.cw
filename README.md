# REST API #

## /drinks/by/day ##

### GET Parameters

#### json

Foces a json response.

**key**: `json`

**value:** *null* | `true`

### start_date

Limit the result set to scans that happened on or after this day.

**key**: `start_date`

**value:** *null* | `YYYY-MM-DD`

### end_date

Limit the result set to scans that happend on or before this day.

**key**: `end_date`

**value:** *null* | `YYYY-MM-DD`

### Output

Here is some example json output with 3 days. Only the first day has scans in it.

```javascript
{
  "drinks_by_day": [
    [
      "2012-09-21",
      [
        {
          "datetime_cst": "2012-09-21 14:57:42 CDT-0500",
          "name": "Red Bull",
          "datetime_gmt_human": "2012-09-21 19:57:42",
          "type_id": 1,
          "scann_id": 1,
          "upc": "611269991000",
          "datetime_cst_human": "2012-09-21 14:57:42",
          "id": 1,
          "datetime": "2012-09-21 19:57:42 UTC+0000"
        },
        {
          "datetime_cst": "2012-09-21 14:57:44 CDT-0500",
          "name": "Red Bull",
          "datetime_gmt_human": "2012-09-21 19:57:44",
          "type_id": 1,
          "scann_id": 2,
          "upc": "611269991000",
          "datetime_cst_human": "2012-09-21 14:57:44",
          "id": 2,
          "datetime": "2012-09-21 19:57:44 UTC+0000"
        },
      ]
    ],
    [
      "2012-09-22",
      []
    ],
    [
      "2012-09-23",
      []
    ]
  ]
}
```
## /drink/*id*/by/day/ ##

### URL Parameters

An integer ID of a consumable.

**key**: `id`

**value:** *integer*


### GET Parameters ###

#### json

Foces a json response.

**key**: `json`

**value:** *null* | `true`

### start_date

Limit the result set to scans that happened on or after this day.

**key**: `start_date`

**value:** *null* | `YYYY-MM-DD`

### end_date

Limit the result set to scans that happend on or before this day.

**key**: `end_date`

**value:** *null* | `YYYY-MM-DD`

List of beverages
/drink/

# Python Stuff #

Creating Database

    from beverages import db
    db.create_all()

Clear Database

    from beverages import db
    db.drop_all()

