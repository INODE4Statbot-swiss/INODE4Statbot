# STATBOT-API

Statbot-API is an API to query SWISS OGD via NL questions.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all dependencies.

```bash
pip install -r docker/requirements.txt
```
create `.env` file and set:
    `OPENAI_API_KEY=[OPENAI_API_KEY]`
## Usage

```bash
python app/main.py
```

## Docs:

Open address `http://127.0.0.1:8000/docs` to read the API doc.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)