import os
from collections import namedtuple, OrderedDict
import json
import argparse
import pandas
from datetime import datetime
import re

InputPaths = namedtuple("InputPaths", ["dict_file", "ann_file", "out_dir"])


class Text():
    class Json():
        VERSION = "version"
        TYPE = "type"
        STANDARD = "STANDARD"
        DATE = "date"
        ANNOTATOR = "annotator"
        DATABASE = "database"
        RECORD = "record"
        THESAURUS = "conclusionThesaurus"
        MCS_THESAURUS = "MCS"
        CONCLUSIONS = "conclusions"
        COMMENT = "comment"
        PTB_XL_ANNOTATORS = "PTB-XL annotators"

    class Csv():
        ECG_ID = "ecg_id"
        SCP_CODES = "scp_codes"
        INFARCTION_STADIUM = "infarction_stadium"
        HEART_AXIS = "heart_axis"
        EXTRA_BEATS = "extra_beats"
        PACEMAKER = "pacemaker"
        JA_PACEMAKER = "ja, pacemaker"
        MI = "MI"
        UNKNOWN = "unknown"

    class Other():
        DATABASE = "PTB-XL"


INFARCTION_COLUMNS = [
    Text.Csv.INFARCTION_STADIUM + "1",  Text.Csv.INFARCTION_STADIUM + "2"
]


def main():
    paths = _parse_args(os.sys.argv)
    annotations = _create_annotations(paths.ann_file, paths.dict_file)
    _write(annotations, paths.out_dir)


def _parse_args(argv):
    parser = argparse.ArgumentParser("PTB-XL annotations")
    parser.add_argument("ann_file")
    parser.add_argument("dict_file")
    parser.add_argument("out_dir")
    paths = parser.parse_args(argv[1:])
    return InputPaths(
        paths.ann_file,
        paths.dict_file,
        paths.out_dir
    )


def _create_annotations(ann_file, dict_file):
    ptbxl_dict = json.load(dict_file)
    table = pandas.read_csv(ann_file)
    annotations = {}
    for _, row in table.iterrows():
        record_name = row[Text.Csv.ECG_ID]
        ann = _init_annotation(record_name)
        ann[Text.Json.COMMENT] = _create_ann_comment(row, ptbxl_dict)
        annotations[record_name] = ann
    return annotations


def _init_annotation(name):
    date = datetime.utcnow().isoformat() + "Z"
    return OrderedDict([
        (Text.Json.VERSION, 1),
        (Text.Json.TYPE, Text.Json.STANDARD),
        (Text.Json.DATE, date),
        (Text.Json.ANNOTATOR, Text.Json.PTB_XL_ANNOTATORS),
        (Text.Json.DATABASE, Text.Other.DATABASE),
        (Text.Json.RECORD, name),
        (Text.Json.THESAURUS, Text.Other.DATABASE),
        (Text.Json.CONCLUSIONS, []),
        (Text.Json.COMMENT, "")
    ])


def _get_record_name(ecg_id):
    return "{0:0>5}_hr".format(ecg_id)


def _write(annotations, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, ann in annotations.items():
        filename = name + ".json"
        with open(filename, "w") as fout:
            json.dump(ann, fout, ensure_ascii=True, indent=2)


def _create_ann_comment(row, ptbxl_dict):
    text = ["Аннотация PTB-XL:", "PTB-XL annotation:"]

    axis = ptbxl_dict[row[Text.Csv.HEART_AXIS]]
    _appent_to_rows(text, axis)

    codes = json.loads(row[Text.Csv.SCP_CODES])
    for code in codes:
        code_text = ptbxl_dict[code]
        if code.endswith(Text.Csv.MI):
            code_text = _add_mi_stage(row, code_text, ptbxl_dict)
        _appent_to_rows(text, code_text)

    extra_beats = row[Text.Csv.EXTRA_BEATS]
    if extra_beats:
        lines = _extra_beat_conclusion(extra_beats)
        _appent_to_rows(text, lines)


def _appent_to_rows(rows, items):
    for i, item in enumerate(items):
        rows[i].append(item)
    return items


def _add_mi_stage(row, mi_text, ptbxl_dict):
    stage_text = None
    for col in INFARCTION_COLUMNS:
        stage = row[col]
        if stage and stage != Text.Csv.UNKNOWN:
            stage_text = ptbxl_dict[stage]
            break
    if stage_text is None:
        return mi_text
    return [stage_text[i] + x[0].lower() + x[1:]
            for (i, x) in enumerate(mi_text)]


def _extract_first_number(text):
    number = 0
    factor = 1
    for c in text:
        if not c.isdiget():
            break
        if number is None:
            number = 0
        number *= factor
        number += int(c)
        factor *= 10
    return number


def _extra_beat_conclusion(extra_beats_text):
    result_text = ["Обнаружены экстрасистолы", "Premature complexes detected"]
    number = _extract_first_number(extra_beats_text)
    if number is None:
        return result_text
    tail = " (%d)" % number
    return [x + tail for x in result_text]


if __name__ == "__main__":
    main()