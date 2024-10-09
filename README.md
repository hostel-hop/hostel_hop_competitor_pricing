# Hostel Spider

This spider is designed to scrape hostel data from specified URLs. It can be run with various arguments to customize the date range and number of URLs to scrape.

## Basic Usage

To run the spider with default settings, use the following command:

## Available Arguments

The spider accepts three optional arguments:

1. `start_date`: The start date for the date range to scrape (format: YYYY-MM-DD)
2. `end_date`: The end date for the date range to scrape (format: YYYY-MM-DD)
3. `url_count`: The number of URLs to scrape from the provided list
4. `use_google_storage`: If set to `True`, the spider will save the output to Google Cloud Storage. If not provided, the spider will save the output to a local file.

### Using Arguments

To use these arguments, add them to the command like this:

```
scrapy crawl hostel_spider -a start_date=2023-05-01 -a end_date=2023-05-10 -a url_count=10 -a use_google_storage=True
```

Replace `YYYY-MM-DD` with the desired dates and `N` with the number of URLs you want to scrape.

## Argument Details and Defaults

### 1. start_date and end_date

These arguments define the date range for which the spider will scrape data.

- **Default**: If not provided, the spider will scrape data for the next 5 days starting from the current date.
- **Example**:

  ```
  scrapy crawl hostel_spider -a start_date=2023-05-01 -a end_date=2023-05-10
  ```

  This will scrape data from May 1, 2023, to May 10, 2023.

### 2. url_count

This argument specifies how many URLs from the provided list should be scraped.

- **Default**: If not provided, the spider will scrape all URLs in the list.
- **Example**:

  ```
  scrapy crawl hostel_spider -a url_count=10
  ```

  This will scrape data from the first 10 URLs in the list.

### 3. use_google_storage

This argument specifies whether the spider should save the output to Google Cloud Storage.

- **Default**: If not provided, the spider will save the output to a local file.
- **Example**:

  ```
  scrapy crawl hostel_spider -a use_google_storage=True
  ```

## Combining Arguments

You can combine all arguments as needed:

```
scrapy crawl hostel_spider -a start_date=2023-05-01 -a end_date=2023-05-10 -a url_count=10 -a use_google_storage=True
```

This will scrape data from May 1, 2023, to May 10, 2023, from the first 10 URLs in the list and save the output to Google Cloud Storage.

## Default Settings

To run the spider with default settings, use the following command:

```
scrapy crawl hostel_spider
```

This will run the spider with default settings. The default settings are:

- Start date: The next 5 days starting from the current date
- End date: None
- URL count: None (scrapes all URLs in the list)
- Use Google Storage: False

## Output

If you set `use_google_storage` to `True`, the spider will save the output to Google Cloud Storage. If not, the spider will save the output to a local file `result.json`.

If you set `use_google_storage` to `True`, you need to run this command to authenticate with gcloud:

```
gcloud auth application-default login
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
