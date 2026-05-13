import pandas as pd

from bots.utbkvip_bot.questions.import_all_csv_questions import (
    insert_question_from_data,
)

EXCEL_PATH = "utbkvip_bot/questions/excel/template_soal2.xlsx"


def import_questions_from_excel(filepath: str, category_guess: str = None):
    imported_total = 0
    failed_rows = 0

    try:
        df = pd.read_excel(filepath)

        # Pastikan semua NaN menjadi string kosong dan semuanya string
        for col in df.columns:
            df[col] = df[col].fillna("").astype(str)

        required_columns = [
            "text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "option_e",
            "correct_option",
        ]

        if not all(col in df.columns for col in required_columns):
            raise ValueError(
                f"❌ File tidak memiliki semua kolom wajib: {', '.join(required_columns)}"
            )

        for index, row in df.iterrows():
            try:
                if not all(str(row.get(col, "")).strip() for col in required_columns):
                    raise ValueError("Field wajib ada yang kosong.")

                insert_question_from_data(
                    question_text=row["text"],
                    option_a=row["option_a"],
                    option_b=row["option_b"],
                    option_c=row["option_c"],
                    option_d=row["option_d"],
                    option_e=row["option_e"],
                    correct_option=row["correct_option"],
                    category=(row.get("category") or category_guess or ""),
                    explanation=row.get("explanation", ""),
                    difficulty=row.get("difficulty", ""),
                    source=row.get("source", ""),
                    sub_category=row.get("sub_category", ""),
                )
                imported_total += 1

            except Exception as e:
                failed_rows += 1
                snippet = str(row.get("text", ""))[:50].replace("\n", " ")
                print(f"⚠️ Gagal impor baris {index + 2}: '{snippet}...' → {e}")

    except Exception as e:
        print(f"❌ Gagal membuka file Excel: {filepath} → {e}")
        return 0, 0

    return imported_total, failed_rows


if __name__ == "__main__":
    total, failed = import_questions_from_excel(EXCEL_PATH)
    print(f"✅ Total impor berhasil: {total}")
    if failed:
        print(f"⚠️ Gagal: {failed}")
