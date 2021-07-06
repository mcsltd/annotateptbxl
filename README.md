# annotateptbxl

The program is used to convert annotations of the PTB-XL database into annotations in the [ecg.ru](ecg.ru) [format](https://github.com/mcsltd/ecganncompare/blob/master/docs/formats.md#input-files-format).

## Resources

Professional tool for physicians and biomedical engineers  
https://ecg.ru/

PTB-XL, a large publicly available electrocardiography dataset  
https://physionet.org/content/ptb-xl/1.0.1/

## Usage

Python (3.4 or later) must be installed on the user's computer to run the program. The program accepts file with PTB-XL annotaions in CSV format, JSON-file with PTB-XL annotation codes description and output directory path. The launch is done through the command line as shown below.

    $ python annotateptbxl.py ann_file dict_file out_dir

- `ann_file` is a path to file in CSV format with PTB-XL annotations;
- `dict_file` is a path to [file](./ptbxl-dict.json) with annotatin codes description organized in dictionary in JSON format;
- `out-dir` is a directory path for result annotation files.

## Output format

The format of the output files are described [there](https://github.com/mcsltd/ecganncompare/blob/master/docs/formats.md#input-files-format).
Annotations from the CSV are converted into text form and written in the `comment` field. The rest of the fields are filled in as follows
- `type`: STANDARD,
- `annotator`: PTB-XL annotators,
- `database`: PTB-XL ECG Dataset,
- `conclusionThesaurus`: PTB-XL,
- `conclusions`: _empty array, []_,
- `record`: _record id_.

### Output file example

```json
{
  "version": 1,
  "type": "STANDARD",
  "date": "2021-06-21T08:35:06.835255Z",
  "annotator": "PTB-XL annotators",
  "database": "PTB-XL ECG Dataset",
  "record": "00001_hr",
  "conclusionThesaurus": "PTB-XL ECG Dataset",
  "conclusions": [],
  "comment": "Аннотация PTB-XL:\nНеопределенная ЭОС\nНормальная ЭКГ\nНизкий вольтаж QRS\nСинусовый ритм\n\nPTB-XL annotation:\nUnknown axis\nNormal ECG\nLow QRS voltages in the frontal and horizontal leads\nSinus rhythm"
}
```
