import argparse
import codecs
import json
import os
import re
from collections import OrderedDict, namedtuple
from datetime import datetime

import pandas as pd

InputPaths = namedtuple("InputPaths", ["ann_file", "dict_file", "out_dir"])


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
        PACE_CODE = "PACE"
        UNK_CODE = "UNK"

    class Other():
        DATABASE = "PTB-XL"


INFARCTION_COLUMNS = [
    Text.Csv.INFARCTION_STADIUM + "1",  Text.Csv.INFARCTION_STADIUM + "2"
]
UTF_8_ENCODING = "utf-8"


def main():
    paths = _parse_args(os.sys.argv)
    ann_table = _read_ann_table(paths.ann_file)
    ptbxl_dict = _read_ptbxl_dict(paths.dict_file)
    annotations = _create_annotations(ann_table, ptbxl_dict)
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


def _create_annotations(ann_table, ptbxl_dict):
    annotations = {}
    for _, row in ann_table.iterrows():
        record_name = _get_record_name(row[Text.Csv.ECG_ID])
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
        # TODO: fix escaped strings
        filename = os.path.join(out_dir, name + ".json")
        with codecs.open(filename, "w", encoding=UTF_8_ENCODING) as fout:
            json.dump(ann, fout, ensure_ascii=False, indent=2)


def _create_ann_comment(row, ptbxl_dict):
    text = [["Аннотация PTB-XL:"], ["PTB-XL annotation:"]]

    axis = ptbxl_dict[row.get(Text.Csv.HEART_AXIS, default=Text.Csv.UNK_CODE)]
    _append_to_rows(text, axis)

    codes = row[Text.Csv.SCP_CODES].replace("'", '"')
    codes = json.loads(codes)
    _check_pacemaker(row, codes)
    for code in codes:
        code_text = ptbxl_dict.get(code)
        if code_text is None:
            continue
        if code.endswith(Text.Csv.MI):
            code_text = _add_mi_stage(row, code_text, ptbxl_dict)
        _append_to_rows(text, code_text)

    extra_beats = row[Text.Csv.EXTRA_BEATS]
    if not pd.isna(extra_beats):
        lines = _extra_beat_conclusion(extra_beats, ptbxl_dict)
        _append_to_rows(text, lines)

    united_lines = ["\n".join(x) for x in text]
    return united_lines[0] + "\n\n" + united_lines[1]


def _append_to_rows(rows, items):
    if not rows:
        return items
    for i, item in enumerate(items):
        rows[i].append(item)
    return items


def _add_mi_stage(row, mi_text, ptbxl_dict):
    stage_text = None
    for col in INFARCTION_COLUMNS:
        stage = row[col]
        if not pd.isna(stage) and stage != Text.Csv.UNKNOWN:
            stage_text = ptbxl_dict[stage]
            break
    if stage_text is None:
        return mi_text
    return [stage_text[i] + x[0].lower() + x[1:]
            for (i, x) in enumerate(mi_text)]


def _extract_first_number(text):
    number = None
    factor = 1
    for c in text:
        if not c.isdigit():
            break
        if number is None:
            number = 0
        number *= factor
        number += int(c)
        factor *= 10
    return number


def _extra_beat_conclusion(extra_beats_text, ptbxl_dict):
    lowercase_dict = {k.lower(): v for k, v in ptbxl_dict.items()}
    lines = []
    for part in re.split(r";|,", extra_beats_text.lower()):
        text = None
        number = _extract_first_number(part)
        if number is None:
            clean_part = _remove_digits(part)
            text = lowercase_dict.get(clean_part)
        else:
            code = part[len(str(number)):]
            raw_text = lowercase_dict[code]
            text = ["{0}: {1}".format(x, number) for x in raw_text]
        if text is not None:
            _append_to_rows(lines, text)
    return lines


def _check_pacemaker(row, codes):
    if Text.Csv.PACE_CODE in codes:
        return
    if row[Text.Csv.PACEMAKER] == Text.Csv.JA_PACEMAKER:
        codes[Text.Csv.PACE_CODE] = 0.0


def _read_ptbxl_dict(path):
    with codecs.open(path, "r", encoding=UTF_8_ENCODING) as fin:
        return json.load(fin)


def _read_ann_table(path):
    ann_table = pd.read_csv(path)
    ann_table[Text.Csv.HEART_AXIS].fillna(Text.Csv.UNK_CODE, inplace=True)
    return ann_table


def _remove_digits(text):
    return "".join(c for c in text if not c.isdigit())


if __name__ == "__main__":
    main()
