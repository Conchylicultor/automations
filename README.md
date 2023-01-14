# Auto-notion

`auto_notion` is an object oriented API (wrapper around `notion_client`).

```python
db = auto_notion.Database('<db_id>')
for row in db:
    row.<field_name> = 'Some text'


db[db.filter.<field_name>.is_empty & db.filter.<field_name> == 5]
```

## Features

* Auto-complete from Colab/Jupyter.
* Auto-generated property names (`"My field"` is available as `row.props.my_field`). This help auto-complete from Colab/Jupyter.
