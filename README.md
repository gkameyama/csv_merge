# CSV Merge for NHT2602

NHT2602 の A/B/C/D 4カテゴリーの CSV ファイルを、列番号の定義に従って 1 つの CSV にまとめる Python スクリプトです。

共通項目は同じ列に縦方向へ結合し、カテゴリーごとに異なる項目は A、B、C、D の順に別々の列へ配置します。

## 対象スクリプト

```powershell
python .\merge_csv_colnum_args.py --a A.csv --b B.csv --c C.csv --d D.csv
```

## 必要なもの

- Python 3
- A/B/C/D それぞれの入力 CSV ファイル
- 入力 CSV は UTF-8 BOM 付き、または UTF-8 として読み込める形式

外部ライブラリは使用していません。

## 使い方

```powershell
cd C:\temp\vscode\csv_merge
python .\merge_csv_colnum_args.py --a .\NHT2602_A0.csv --b .\NHT2602_B0.csv --c .\NHT2602_C0.csv --d .\NHT2602_D0.csv
```

出力先を指定する場合は `-o` または `--output` を使います。

```powershell
python .\merge_csv_colnum_args.py --a .\NHT2602_A0.csv --b .\NHT2602_B0.csv --c .\NHT2602_C0.csv --d .\NHT2602_D0.csv -o .\NHT2602_data_all.csv
```

## 引数

| 引数 | 必須 | 内容 |
| --- | --- | --- |
| `--a` | はい | カテゴリー A の CSV ファイルパス |
| `--b` | はい | カテゴリー B の CSV ファイルパス |
| `--c` | はい | カテゴリー C の CSV ファイルパス |
| `--d` | はい | カテゴリー D の CSV ファイルパス |
| `-o`, `--output` | いいえ | 出力 CSV ファイルパス |

`--output` を省略した場合は、実行時刻を使って `csv_merge_MMDDHHMM.csv` という名前で出力します。

同名ファイルがすでに存在する場合は上書きせず、`_2`、`_3` のような連番を付けて保存します。

## 出力仕様

- 出力 CSV の文字コードは Shift_JIS です。
- 1行目にヘッダーを出力します。
- 先頭列のヘッダー名は `SAMPLENUMBER` に変更します。
- `SAMPLENUMBER` の昇順でソートして出力します。
- `SAMPLENUMBER` が 1 桁の数字だけの行は、ダミーデータとして除外します。

## 列の結合ルール

入力 CSV の列番号は 1 始まりで扱います。

| 区分 | A | B | C | D |
| --- | --- | --- | --- | --- |
| 共通列 | 1-3637 | 1-3637 | 1-3637 | 1-3637 |
| カテゴリー別メイン列 | 3638-9971 | 3638-7182 | 3638-9168 | 3638-7256 |
| V列 | 9972-10233 | 7183-7444 | 9169-9430 | 7257-7518 |
| Aのみ末尾列 | 10234-10362 | - | - | - |

出力 CSV では、共通列の後ろにカテゴリー別メイン列を A、B、C、D の順で配置します。

V列と A の末尾列は、A ファイルのヘッダーを使って出力ヘッダーを作成します。

## 処理内容

1. A/B/C/D の入力ファイルが存在するか確認します。
2. 各 CSV のヘッダー行を読み込みます。
3. 必要な列数が足りているか確認します。
4. 出力ヘッダーを作成します。
5. 各カテゴリーのデータ行を出力用の列位置へ配置します。
6. `SAMPLENUMBER` でソートします。
7. 1 桁数字の `SAMPLENUMBER` を持つ行を除外します。
8. CSV を出力します。

## エラー例

入力ファイルが見つからない場合:

```text
Category A file not found: ...
```

必要な列数が足りない場合:

```text
Category A has 100 columns, but column 10362 is required.
```

データ行の列数が足りない場合:

```text
Category A row 2 has 100 columns, but column 10362 is required.
```

## 文字コードを変更したい場合

出力文字コードは `merge_csv_colnum_args.py` 内の `OUTPUT_ENCODING` で指定しています。

```python
OUTPUT_ENCODING = "shift_jis"
# OUTPUT_ENCODING = "utf-8-sig"
```

UTF-8 BOM 付きで出力したい場合は、上の行をコメントアウトし、下の行を有効にしてください。
