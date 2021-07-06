# annotateptbxl

The program is used to convert annotations of the PTB-XL database into annotations in the ecg.ru [format](https://github.com/mcsltd/ecganncompare/blob/master/docs/formats.md).

## Resources

Professional tool for physicians and biomedical engineers  
https://ecg.ru/

PTB-XL, a large publicly available electrocardiography dataset  
https://physionet.org/content/ptb-xl/1.0.1/

## Usage

Python (3.4 or later) must be installed on the user's computer to run the program. The program accepts file with PTB-XL annotaions in CSV format, JSON-file with PTB-XL annotation codes description and path to output directory. The format of the output files are described [there](https://github.com/mcsltd/ecganncompare/blob/master/docs/formats.md). The launch is done through the command line as shown below.

    $ python annotateptbxl.py ann_file dict_file out_dir

- `ann_file` is a path to file in CSV format with PTB-XL annotations;
- `dict_file` is a path to [file](./ptbxl-dict.json) with annotatin codes description organized in dictionary in JSON format;
- `out-dir` is a directory path for result annotation files.
