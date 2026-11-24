"""Create the Vietnamese progress report with the bundled python-docx runtime."""
from datetime import datetime
from pathlib import Path
import json
import re

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[4]
ML = ROOT/'e-commerce/ml/recommendation'
OUTPUT = ML/'reports/Bao_cao_tien_do_ML_Recommendation_24_11_2026.docx'


def shade(cell, fill):
    element = OxmlElement('w:shd')
    element.set(qn('w:fill'),fill)
    cell._tc.get_or_add_tcPr().append(element)


def main():
    eda = json.loads((ML/'artifacts/kaggle-eda-latest/fashion-reco/output/eda.json').read_text(encoding='utf-8'))
    current = json.loads((ROOT/'recommendation-demo/data/tiki-fashion-20000/tiki-fashion.manifest.json').read_text(encoding='utf-8'))
    document = Document()
    section = document.sections[0]
    section.page_width,section.page_height = Inches(8.5),Inches(11)
    section.top_margin,section.bottom_margin = Inches(.7),Inches(.65)
    section.left_margin,section.right_margin = Inches(.8),Inches(.8)
    for name in ('Normal','Title','Subtitle','Heading 1','Heading 2'):
        style=document.styles[name]
        style.font.name='Times New Roman'
        style.font.color.rgb=RGBColor(0,0,0)
        style._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Times New Roman')
    normal=document.styles['Normal']
    normal.font.size=Pt(11)
    normal.paragraph_format.space_after=Pt(6)
    normal.paragraph_format.line_spacing=1.12
    for name,size in [('Title',22),('Heading 1',15),('Heading 2',12)]:
        document.styles[name].font.size=Pt(size)
    document.styles['Heading 1'].paragraph_format.space_before=Pt(8)
    document.styles['Heading 1'].paragraph_format.space_after=Pt(7)
    footer=section.footer.paragraphs[0]
    footer.alignment=2
    run=footer.add_run('ML Recommendation  |  ')
    run.font.size=Pt(9)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)

    def paragraph(text, bold=False):
        p=document.add_paragraph()
        p.add_run(re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))','.',text)).bold=bold
        return p

    def heading(text):
        document.add_heading(text,level=1)

    def table(headers, rows, widths):
        t=document.add_table(rows=1, cols=len(headers))
        t.alignment=WD_TABLE_ALIGNMENT.CENTER
        t.autofit=False
        for cell,width,text in zip(t.rows[0].cells,widths,headers):
            cell.width=Inches(width);cell.text=text;shade(cell,'243746')
            for run in cell.paragraphs[0].runs:run.bold=True;run.font.color.rgb=RGBColor(255,255,255)
        repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for index,row in enumerate(rows):
            cells=t.add_row().cells
            for cell,width,value in zip(cells,widths,row):
                cell.width=Inches(width);cell.text=re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))','.',str(value))
                cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if index%2==0:shade(cell,'F2F5F7')
        borders=OxmlElement('w:tblBorders')
        for side in ('top','left','bottom','right','insideH','insideV'):
            el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
        t._tbl.tblPr.append(borders)
        for row in t.rows:
            tr=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(tr)
            for cell in row.cells:
                margins=OxmlElement('w:tcMar')
                for side in ('top','bottom','left','right'):
                    el=OxmlElement('w:'+side);el.set(qn('w:w'),'85');el.set(qn('w:type'),'dxa');margins.append(el)
                cell._tc.get_or_add_tcPr().append(margins)
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
                    p.paragraph_format.line_spacing=1.05
                    for r in p.runs:r.font.size=Pt(10.5)
        document.add_paragraph().paragraph_format.space_after=Pt(0)

    document.add_paragraph('Báo cáo tiến độ ML recommendation',style='Title')
    paragraph('Dự án E-commerce Recommendation • Bộ môn Kiến trúc hướng dịch vụ')
    paragraph('Ngày báo cáo 24 tháng 11 năm 2026 • Nhánh feature/ml-recommendation')
    paragraph('Báo cáo tổng hợp phần thu thập dữ liệu, xây dựng pipeline thực nghiệm, triển khai Kaggle và kết quả EDA đã xác minh. Đã có code và môi trường để so sánh mô hình; chưa có kết quả training chính thức vì nhãn phù hợp cần được nhóm chấm.')
    heading('1 Mục tiêu và phạm vi đã chốt')
    paragraph('Hệ thống nhận nhu cầu mua sắm đã được làm rõ, các loại món cần mua, món đã có và tổng ngân sách; tìm ứng viên, xếp hạng rồi chọn một bộ sản phẩm kèm giá và ảnh minh họa. Ví dụ: đi ăn cưới, đã có váy, cần giày và túi với tổng ngân sách 700.000 đồng.')
    paragraph('Ngân sách trong thực nghiệm là tổng giá sản phẩm của cả bộ, chưa gồm vận chuyển và khuyến mãi. Đây là phạm vi mở rộng so với SPEC hiện có dùng trần giá từng món; cần đồng bộ tài liệu trước khi tích hợp backend.')
    table(['Thành phần','Trạng thái tại thời điểm báo cáo'],[
        ('Catalog và crawler','Đã có dữ liệu; tiếp tục bổ sung quần áo và váy.'),
        ('Code ML và notebook','Đã triển khai trong e-commerce/ml/recommendation.'),
        ('EDA trên Kaggle','Phiên bản 3 hoàn tất trên snapshot 13.538 sản phẩm.'),
        ('Tạo tập ứng viên chấm nhãn','Đã gửi lượt GPU riêng; chưa xác nhận hoàn tất.'),
        ('Training và chọn model thắng','Chưa thực hiện trên dữ liệu có nhãn thật.')],[1.9,4.9])
    paragraph('Tác vụ nặng chạy trên Kaggle. Máy cá nhân dùng để chuẩn bị code, truyền dữ liệu và chạy kiểm thử nhỏ. Ảnh hiện là URL sản phẩm; chưa triển khai ảnh tham chiếu đầu vào, LLM hội thoại hoặc cá nhân hóa từ lịch sử khách hàng.')

    document.add_page_break()
    heading('2 Dữ liệu đã thu thập và kết quả EDA')
    paragraph(f"Bộ ban đầu có 10.000 sản phẩm giày, túi, balo/vali và phụ kiện. Lượt bổ sung lấy quần áo, váy/đầm nam nữ trực tiếp từ Tiki. Manifest cục bộ gần nhất ghi nhận {current['productCount']:,} sản phẩm, gồm {current['addedCount']:,} sản phẩm bổ sung. Con số này là tiến độ thu thập; chưa đủ mục tiêu 20.000 và khác snapshot EDA đã đóng băng.")
    paragraph('File hợp nhất: recommendation-demo/data/tiki-fashion-20000/tiki-fashion.enriched.json. Crawler lưu checkpoint, loại ID trùng, giữ giá và trạng thái nguồn; tiến trình giám sát chờ 3 phút để chạy lại khi lượt tải dừng. Cơ chế hoạt động khi máy còn bật, không bảo đảm chạy qua lần khởi động lại máy.')
    table(['Chỉ tiêu trên snapshot Kaggle','Kết quả đã xác minh'],[
        ('Sản phẩm đầu vào và hợp lệ',f"{eda['raw_count']:,} / {eda['valid_count']:,}"),
        ('Available',f"{eda['inventory_statuses']['available']:,}"),
        ('Out of stock',f"{eda['inventory_statuses']['out_of_stock']:,}"),
        ('Upcoming',f"{eda['inventory_statuses']['upcoming']:,}"),
        ('Thiếu mô tả hoặc URL ảnh','0 / 0'),
        ('URL ảnh đại diện khác nhau',f"{eda['unique_images']:,}"),
        ('Giá thấp nhất và trung vị','1.000 VND / 175.000 VND'),
        ('Phân vị giá 95 và giá cao nhất','1.450.000 VND / 19.800.000 VND')],[3.6,3.2])
    paragraph('Trong 120 nhu cầu mẫu có 243 cặp nhu cầu và loại món. Chế độ research có 2 cặp thiếu ứng viên; available_only có 4 cặp thiếu ứng viên. Các trường hợp này tập trung ở nhu cầu ngân sách rất thấp, được giữ để kiểm tra khả năng báo không có kết quả.')
    paragraph('Bộ dữ liệu không có user ID hoặc lịch sử xem, thêm giỏ và mua hàng. Điểm đánh giá và số bán tổng hợp không thay thế dữ liệu tương tác user–item. Nhóm thu thập theo truy vấn cần kiểm tra ngữ nghĩa thủ công; có URL ảnh không đồng nghĩa đã xác minh mọi ảnh hoặc mọi mô tả.')
    paragraph('Research cho phép dùng sản phẩm hết hàng để đánh giá liên quan nội dung. Available_only chỉ dùng snapshot được nguồn báo available. Không sửa trạng thái nguồn để làm đẹp kết quả; snapshot cũng không bảo đảm tồn kho thực tế tại thời điểm người dùng mua.')

    document.add_page_break()
    heading('3 Code và quy trình thực nghiệm đã triển khai')
    paragraph('Code đặt tại e-commerce/ml/recommendation trên nhánh feature/ml-recommendation. Package fashion_reco tách logic dùng chung khỏi notebook; chưa thay đổi API marketplace.')
    table(['Notebook','Nội dung'],[
        ('01 EDA preprocessing','Đọc snapshot, kiểm tra dữ liệu, giá và độ phủ nhu cầu; xuất JSON, CSV và báo cáo HTML.'),
        ('02 Labeling dataset','Tạo embedding, gộp ứng viên và xuất CSV không có nhãn tự sinh.'),
        ('03 Train evaluate inference','Huấn luyện, so sánh trên validation, khóa cấu hình và đánh giá test.')],[2.1,4.7])
    paragraph('Package có các phần data, schemas, candidates, features, models, training, evaluation, eligibility, bundle và inference. Cấu hình thí nghiệm nằm trong configs/experiment.yaml; artifact lớn và môi trường Python được loại khỏi Git.')
    table(['Phương pháp','Vai trò trong so sánh'],[
        ('TF-IDF và BM25','Baseline tìm kiếm theo từ khóa.'),
        ('Multilingual E5-base','Truy xuất ngữ nghĩa bằng mô hình pretrained.'),
        ('BGE-M3','Truy xuất ngữ nghĩa đa ngôn ngữ, đối chứng với E5.'),
        ('LambdaMART','Ranker có giám sát, học từ feature từ khóa, ngữ nghĩa và sản phẩm.')],[2.1,4.7])
    paragraph('Feature gồm điểm TF-IDF/BM25/E5/BGE, khớp tên và thương hiệu, loại món, log giá, tỷ lệ giá/ngân sách, rating, số review và cờ thiếu. Không tạo giả lượt xem, doanh số theo ngày hoặc số lượng tồn kho. E5 và BGE đã ghim revision cụ thể để tái lập.')
    paragraph('Đã chuẩn bị 120 nhu cầu mẫu từ 40 tình huống với ba mức ngân sách; chưa phải truy vấn thu thập từ người dùng thật. Chia 72 train, 24 validation và 24 test theo family_id, giữ các biến thể cùng tình huống trong một tập.')
    paragraph('Tập gộp tối đa 60 ứng viên cho mỗi nhu cầu, phân bổ theo loại món. Nhãn 0–3 do nhóm chấm; ô chưa chấm không coi là 0. Hai người chấm test độc lập, xử lý bất đồng trước khi dùng. Training không đọc nhãn test và từ chối dữ liệu thiếu nhãn.')

    document.add_page_break()
    heading('4 Đánh giá và kiểm chứng kỹ thuật')
    paragraph('Xếp hạng được so sánh trên cùng tập ứng viên bằng NDCG@5 và Precision@5. Recall báo theo tập gộp đã chấm, không tuyên bố Recall toàn catalog. Validation dùng để chọn cấu hình; test chỉ mở sau khi khóa lựa chọn.')
    paragraph('Bộ chọn xét tối đa 20 ứng viên cho mỗi loại món và tối đa bốn loại món. Bộ đầy đủ phải có đúng một sản phẩm cho mỗi loại, không trùng ID và tổng giá không vượt ngân sách. Không tìm được bộ trong tập ứng viên thì trả lý do và lựa chọn từng phần, không khẳng định toàn sàn không có hàng phù hợp.')
    paragraph('Báo cáo sẽ có tỷ lệ đủ món, vi phạm ngân sách, fallback, độ trễ và tài nguyên; nhóm chấm riêng mức đáp ứng nhu cầu và tính tương thích của bộ. Chưa có mô hình học phối đồ, kiểm tra cỡ mặc hoặc bảo đảm thẩm mỹ.')
    table(['Kiểm chứng đã thực hiện','Kết quả'],[
        ('Kiểm thử fixture nhỏ','18 kiểm thử đạt; không train catalog thật trên máy cá nhân.'),
        ('Lọc và chọn bộ','Kiểm tra biên ngân sách, hết hàng, thiếu món, loại sai và trùng ID.'),
        ('Nhãn và chia tập','Kiểm tra thiếu nhãn, thay snapshot, rò rỉ family và bất đồng người chấm.'),
        ('Artifact và bootstrap','Đọc lại TF-IDF/BM25; nhận cả ZIP và thư mục Kaggle đã giải nén.'),
        ('EDA từ xa','Phiên bản 3 hoàn tất; hash đầu vào khớp snapshot upload.')],[2.1,4.7])
    paragraph('Các lỗi triển khai đã xử lý: thiếu thư viện six khi cài Kaggle CLI; timeout đường IPv6 được khắc phục bằng wrapper IPv4 riêng; Kaggle tự giải nén ZIP; pip không cài được build dependencies. EDA hiện chạy trực tiếp từ source bằng thư viện chuẩn, không cần pip.')
    paragraph('Lượt GPU riêng đã được gửi tới notebook soa-fashion-labeling để tạo embedding và file chấm nhãn. Trạng thái cuối được kiểm tra là RUNNING; chưa có xác nhận COMPLETE hoặc file nhãn tải về. Lần bật tiến trình giám sát tự tải output chưa thực hiện được do giới hạn sử dụng của công cụ xét duyệt.')

    document.add_page_break()
    heading('5 Kết quả bàn giao và việc cần làm tiếp')
    paragraph('Đã bàn giao source package, ba notebook, nhu cầu mẫu, cấu hình thí nghiệm, bộ kiểm thử và workspace Kaggle riêng tư. Chưa có model được chứng minh tốt nhất, chưa fine-tune encoder và chưa tích hợp inference vào backend.')
    table(['Ưu tiên','Việc tiếp theo','Điều kiện hoàn tất'],[
        ('1','Kiểm tra lượt GPU tạo tập nhãn','Có pool-manifest và CSV chấm điểm, kiểm tra đúng hash snapshot.'),
        ('2','Nhóm duyệt nhu cầu và ứng viên','Duyệt loại món, ngân sách, mô tả/ảnh; chốt snapshot dùng chính thức.'),
        ('3','Chấm nhãn thật','Train/validation đủ điểm; test có hai người chấm và giải quyết bất đồng.'),
        ('4','Train và so sánh trên Kaggle','Chạy các baseline và LambdaMART; lưu số liệu kể cả khi baseline thắng.'),
        ('5','Đánh giá bộ và chọn phương án','Đối chiếu chất lượng, ngân sách, tốc độ và tài nguyên.'),
        ('6','Tích hợp backend','Nạp artifact đã tạo, không tính lại catalog hoặc train mỗi request.')],[.6,2.8,3.4])
    paragraph('Crawler có thể tiếp tục hướng tới 20.000 trong lúc nghiên cứu. Nếu đổi catalog sau khi đã chấm nhãn, phải tạo snapshot và pool mới hoặc có quy trình ánh xạ kiểm chứng; không trộn nhãn và kết quả của các phiên bản khác nhau.')
    document.add_heading('Tệp và vị trí đối chiếu',level=2)
    for text in [
        'Source và hướng dẫn: e-commerce/ml/recommendation/README.md',
        'Notebook: e-commerce/ml/recommendation/notebooks/',
        'Workspace upload: e-commerce/ml/recommendation/artifacts/upload-v1/',
        'EDA đã tải về: artifacts/kaggle-eda-latest/fashion-reco/output/ bên trong module ML.',
        'Kaggle dataset riêng tư: https://www.kaggle.com/datasets/charlotte4306/soa-ml-workspace',
        'Kaggle EDA: https://www.kaggle.com/code/charlotte4306/soa-fashion-recommendation-experiments',
        'Kaggle tạo nhãn: https://www.kaggle.com/code/charlotte4306/soa-fashion-labeling',
    ]:
        p=paragraph(text)
        for run in p.runs:run.font.size=Pt(10)
    paragraph('Các số liệu EDA trong báo cáo lấy từ eda.json và catalog-manifest.json của phiên Kaggle đã hoàn tất. Tiến độ tổng dữ liệu lấy từ manifest cục bộ khi tạo báo cáo. Báo cáo không sử dụng số liệu chất lượng mô hình hoặc nhãn giả lập làm kết quả thực nghiệm.')
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    document.save(OUTPUT)
    print(OUTPUT)


if __name__=='__main__':
    main()
