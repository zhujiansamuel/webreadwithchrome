from funtions import *

if __name__ == "__main__":
    qa_generator = QAGeneration()

    org_txt = "金沢大学の外の眺めが綺麗ですね。彼が学校に行きました。太郎は金沢大学で勉強します。"
    print("original text:", org_txt)
    results = qa_generator.generate_QA(org_txt)
    print(results)

    for q,a in results:
        print(' Q : ',q)
        print(' A : ',a)
        print()