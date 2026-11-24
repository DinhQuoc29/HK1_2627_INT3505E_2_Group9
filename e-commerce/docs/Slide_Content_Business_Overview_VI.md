# Nội dung slide — Tổng quan nghiệp vụ Marketplace

> Bản nháp nội dung để chuyển thành slide thuyết trình. Phạm vi dựa trên tài liệu dự án hiện có; V1 và V2 được giữ đúng như tài liệu đặc tả. Nội dung ghi “đề xuất” là gợi ý trình bày, không phải cam kết hoặc số liệu đã đo của dự án.

## Slide 1 — Marketplace đa nhà bán: khám phá, mua và hoàn tất đơn hàng

**Thông điệp chính:** Xây dựng một marketplace kết nối người mua với nhiều cửa hàng, hỗ trợ khám phá sản phẩm bằng tìm kiếm và gợi ý, sau đó xử lý giỏ hàng, đơn hàng và giao nhận theo từng cửa hàng.

- Người mua: tìm sản phẩm, nhận gợi ý, đặt và theo dõi đơn.
- Người bán: đăng sản phẩm, quản lý giá/tồn kho và cập nhật giao hàng.
- Quản trị viên: quản lý danh mục; trong V2 có thêm kiểm duyệt.
- Phạm vi V1 có gợi ý sản phẩm; V2 mở rộng trợ lý hội thoại, đánh giá và kiểm duyệt.

**Gợi ý hình:** Sơ đồ ba vai trò — Buyer, Seller, Admin — cùng kết nối vào Marketplace.

**Ghi chú thuyết trình:** Đây là marketplace nhiều cửa hàng, vì vậy trải nghiệm mua nằm ở một nền tảng chung nhưng mỗi cửa hàng vẫn chịu trách nhiệm với listing, tồn kho và phần đơn hàng của mình.

## Slide 2 — Bài toán và giá trị nghiệp vụ

**Thông điệp chính:** Giúp người mua tìm được sản phẩm phù hợp và giúp nhà bán quản lý giao dịch trong một luồng thống nhất.

- Danh mục và bộ lọc giúp thu hẹp lựa chọn theo giá, thương hiệu, tỉnh/thành và danh mục.
- Gợi ý cá nhân hóa, sản phẩm tương tự và danh sách phổ biến hỗ trợ khám phá sản phẩm.
- Một giỏ hàng có thể chứa sản phẩm từ nhiều cửa hàng.
- Đơn hàng và giao nhận được theo dõi riêng theo từng cửa hàng.
- Quản trị viên duy trì cấu trúc danh mục chung để người bán phân loại và người mua duyệt sản phẩm.

**Gợi ý hình:** Hai cột “Nhu cầu người mua” và “Nhu cầu nhà bán”, nối vào nền tảng chung.

**Ghi chú thuyết trình:** Giá trị của marketplace đến từ việc nối liền khám phá sản phẩm với vận hành đơn hàng đa cửa hàng. Tài liệu hiện chưa đặt chỉ tiêu kinh doanh định lượng.

## Slide 3 — Các bên tham gia và trách nhiệm

| Vai trò | Trách nhiệm chính trong V1 | Mở rộng V2 |
|---|---|---|
| Người mua | Đăng nhập; tìm và xem listing; nhận gợi ý; quản lý giỏ; thanh toán mô phỏng; theo dõi hoặc hủy đơn đủ điều kiện | Hỏi trợ lý mua sắm; xem và gửi đánh giá sau khi đơn hoàn tất |
| Người bán | Đăng, sửa hoặc ngừng bán listing của cửa hàng; cập nhật tồn kho; xem và xử lý đơn của cửa hàng; cập nhật trạng thái giao hàng | Không có luồng seller mới được xác định trong tài liệu hiện tại |
| Quản trị viên | Tạo, đổi tên và sắp xếp danh mục cha-con | Kiểm duyệt đánh giá bị báo cáo và listing bị gắn cờ |

**Nguyên tắc phân quyền:** Người mua chỉ truy cập giỏ và đơn hàng của mình; người bán chỉ thao tác trên cửa hàng được phân quyền; thao tác quản trị yêu cầu quyền admin.

**Ghi chú thuyết trình:** Mỗi vai trò có phạm vi thao tác rõ để bảo vệ dữ liệu người mua và tài sản của từng cửa hàng.

## Slide 4 — Luồng nghiệp vụ đầu-cuối của người mua

1. **Truy cập:** đăng ký/đăng nhập bằng email và mật khẩu; người mua hiện có thể dùng Google sign-in.
2. **Khám phá:** duyệt cây danh mục hoặc tìm theo tên; lọc giá, thương hiệu, tỉnh/thành; mở trang listing.
3. **Chọn sản phẩm:** xem ảnh, giá hiện tại, cửa hàng bán và tình trạng còn hàng; thêm sản phẩm từ một hoặc nhiều shop vào giỏ.
4. **Xác nhận giỏ:** xem sản phẩm được nhóm theo shop và giá hiện tại.
5. **Checkout:** hệ thống kiểm tra lại giá và tồn kho. Nếu giá đổi, người mua xem giá mới và xác nhận lại.
6. **Mua hàng:** một lần checkout tạo một đơn cho mỗi shop; hệ thống hiển thị một khoản thanh toán mô phỏng được phân bổ cho các đơn.
7. **Sau mua:** xem trạng thái từng đơn shop; có thể hủy riêng đơn còn đủ điều kiện.

**Gợi ý hình:** Quy trình ngang 7 bước, nhấn vào điểm “kiểm tra lại giá/tồn kho” trước checkout.

**Ghi chú thuyết trình:** Checkout là điểm kiểm soát quan trọng: nếu bất kỳ mặt hàng nào không còn đủ tồn kho, toàn bộ checkout thất bại và không đơn hàng, thanh toán hay khấu trừ tồn kho nào được giữ lại.

## Slide 5 — Một giỏ hàng, nhiều đơn theo cửa hàng

**Ví dụ minh họa:** Giỏ có sản phẩm của Shop A trị giá 600.000₫ và Shop B trị giá 400.000₫.

- Người mua xác nhận giỏ một lần.
- Marketplace tạo hai đơn riêng: đơn Shop A và đơn Shop B.
- Ghi nhận một khoản thanh toán mô phỏng 1.000.000₫, phân bổ 600.000₫ và 400.000₫ theo từng đơn.
- Mỗi người bán chỉ xem và cập nhật đơn thuộc shop của mình.
- Người mua theo dõi trạng thái riêng từng đơn; hủy một đơn không làm thay đổi đơn shop còn lại.
- Thử lại cùng một xác nhận checkout không được tạo thêm đơn, thanh toán hoặc khấu trừ tồn kho.

**Gợi ý hình:** Một giỏ → “Payment” → Order A + Order B; mỗi order nối đến shop tương ứng.

**Lưu ý:** Thanh toán ở V1 dùng tiền mô phỏng; tài liệu không mô tả tích hợp thẻ, chuyển khoản ngân hàng hoặc chi trả thực tế cho shop.

## Slide 6 — Vận hành của người bán và quản trị viên

**Người bán**

- Tạo listing với tên, mô tả, danh mục, ảnh, giá và số lượng tồn kho.
- Cập nhật thông tin, giá và tồn kho; ngừng bán khi cần.
- Chịu trách nhiệm báo kịp thời thay đổi tồn kho phát sinh ngoài nền tảng, như bán tại cửa hàng hoặc hàng hư hỏng.
- Xem các mặt hàng trong đơn đến và cập nhật trạng thái giao hàng sau khi gửi hàng.

**Quản trị viên**

- Tạo/đổi tên danh mục và gán danh mục cha để duy trì cây danh mục.
- V2: xem ngữ cảnh đánh giá/listing bị báo cáo hoặc gắn cờ, rồi giữ lại hoặc gỡ/ngừng bán theo tiêu chí đã thống nhất.

**Ghi chú thuyết trình:** Dữ liệu tồn kho vật lý phụ thuộc vào việc người bán cập nhật đúng và kịp thời. Listing bị rút khỏi bán không được dùng cho đơn mới, nhưng thông tin lịch sử đơn hàng phải được giữ nguyên.

## Slide 7 — Tìm kiếm và gợi ý sản phẩm

**Tìm kiếm V1**

- Lấy các listing phù hợp với truy vấn và bộ lọc đã chọn.
- Xếp hạng nền theo độ khớp: tên chính xác trước, sau đó tên/thuộc tính, cuối cùng là mô tả; xử lý đồng hạng theo độ phổ biến rồi mã listing.
- ML có thể xếp hạng lại cùng tập ứng viên; khi ML lỗi hoặc quá thời gian, trả về thứ tự baseline.
- Đánh giá baseline và ML trên cùng truy vấn/candidate được gán nhãn; tài liệu đề xuất báo cáo NDCG@5.

**Gợi ý V1**

- Gợi ý trang chủ có thể dựa trên lịch sử/ưu tiên được phép sử dụng; sản phẩm tương tự dựa trên thuộc tính catalog.
- Người mới, lỗi model hoặc timeout dùng danh sách sản phẩm phổ biến làm fallback.
- Trước khi trả kết quả, mọi nhánh đều phải lọc listing đang bán, còn hàng và không vượt ngân sách tối đa cho mỗi sản phẩm nếu người mua nhập.
- Khi tắt cá nhân hóa, dừng ghi nhận sự kiện và không dùng lịch sử mua sắm cho gợi ý trên các thiết bị đăng nhập cùng tài khoản.

**Ghi chú thuyết trình:** Fallback cũng phải qua điều kiện về trạng thái bán, tồn kho và ngân sách; không được đề xuất hàng hết hoặc vượt ngân sách chỉ vì model gặp lỗi.

## Slide 8 — Vai trò AI/ML: hướng tiếp cận và giới hạn bằng chứng

- Tài liệu dự án đặt ML ở hai vị trí có kiểm soát: xếp hạng lại kết quả tìm kiếm và cá nhân hóa gợi ý.
- Phải có baseline chạy được trước; ML được so sánh với baseline trên cùng tập truy vấn và sản phẩm ứng viên.
- Bài báo tham khảo khảo sát GNB, Decision Tree, Random Forest, Logistic Regression và PCA; tác giả báo cáo Random Forest có kết quả tốt nhất trên bộ dữ liệu của họ.
- Bộ dữ liệu bài báo là dữ liệu khảo sát/hành vi với 11 trường, chia train/test 75/25; đây không phải dữ liệu benchmark của dự án.
- Bài báo có số accuracy không nhất quán giữa phần tóm tắt và kết quả chi tiết (99,6% và 99,8%). Không dùng các con số này làm kết quả hoặc cam kết của marketplace.

**Gợi ý hình:** “Candidate retrieval → Baseline → ML reranking (optional) → Eligibility filter → Results”, nhánh lỗi ML quay về baseline/popular.

**Ghi chú thuyết trình:** Bài báo đóng vai trò tài liệu tham khảo thuật toán, không chứng minh mô hình của dự án đã đạt độ chính xác tương tự. Kết quả cần được đánh giá trên truy vấn và catalog phù hợp với marketplace.

## Slide 9 — Niềm tin, quyền riêng tư và tính toàn vẹn giao dịch

- **Bảo vệ tài khoản:** phiên đăng nhập bị vô hiệu khi logout; thao tác được giới hạn theo người mua, shop và vai trò admin.
- **Giá/tồn kho chính xác:** checkout kiểm tra lại giá và số lượng; giá đổi cần người mua xác nhận.
- **Không oversell:** checkout đa shop được xử lý theo giao dịch nguyên tử; nếu một dòng hàng thất bại, hoàn tác toàn bộ.
- **Chống giao dịch trùng:** khóa idempotency làm cho cùng xác nhận chỉ tạo một kết quả mua hàng.
- **Lịch sử minh bạch:** tên và giá sản phẩm tại thời điểm mua được lưu vào dòng đơn, không thay đổi khi listing sửa sau này.
- **Quyền riêng tư:** lựa chọn tắt cá nhân hóa áp dụng trên các thiết bị dùng chung tài khoản và không ngăn cản việc mua sắm.

**Gợi ý hình:** Sáu “lớp bảo vệ” quanh luồng checkout.

**Ghi chú thuyết trình:** Các yêu cầu này bảo vệ ba thứ: quyền truy cập dữ liệu, số lượng hàng thực bán được và tính nhất quán giữa đơn hàng với khoản thanh toán mô phỏng.

## Slide 10 — Phạm vi phát hành

| V1 — First release | V2 — Deferred |
|---|---|
| Đăng nhập và phân quyền | Trợ lý mua sắm bằng hội thoại, hỏi lại khi yêu cầu chưa rõ |
| Danh mục và listing | Giải thích gợi ý bằng thông tin có trong catalog |
| Duyệt/tìm kiếm, lọc và xếp hạng baseline; đánh giá ML theo baseline | Gửi, xem và lọc theo đánh giá sản phẩm |
| Gợi ý trang chủ, sản phẩm tương tự, sản phẩm phổ biến; ngân sách và tắt cá nhân hóa | Chỉ người mua sản phẩm trong đơn đã hoàn tất mới được đánh giá; admin kiểm duyệt review |
| Giỏ đa shop, checkout mô phỏng, đơn tách theo shop, theo dõi/hủy theo điều kiện | Admin kiểm duyệt listing bị gắn cờ |

**Thông điệp:** V1 ưu tiên khép kín luồng mua và xử lý đơn đa shop. V2 bổ sung trải nghiệm tư vấn và các luồng phụ thuộc dữ liệu đánh giá.

## Slide 11 — Rủi ro nghiệp vụ và quyết định còn mở

**Rủi ro trọng yếu và cách kiểm soát trong đặc tả**

- Tồn kho ngoài đời thay đổi nhưng cập nhật chậm → người bán cần đối soát; checkout chỉ chấp nhận lượng tồn khả dụng.
- Giá/listing thay đổi khi sản phẩm đang trong giỏ → tải lại giá và tồn kho khi xác nhận; giá mới cần xác nhận lại.
- Hai người mua cùng lấy đơn vị cuối hoặc lỗi giữa checkout đa shop → cập nhật tồn/đơn/thanh toán trong cùng transaction và rollback nếu lỗi.
- Timeout hoặc người mới không có lịch sử → fallback baseline/popular; lọc lại điều kiện hợp lệ trước khi trả kết quả.
- Hủy đơn lặp hoặc đua với cập nhật giao hàng → cập nhật trạng thái, hoàn tồn và điều chỉnh phân bổ đúng một lần.

**Ba quyết định nghiệp vụ cần chốt trước khi hoàn thiện acceptance**

1. Đơn được hủy đến trạng thái nào, và người bán ghi nhận dispatch ở thời điểm nào so với bàn giao thực tế?
2. Sự kiện nào xác định đơn “đã hoàn tất” để mở quyền đánh giá, và ai được phép xác nhận?
3. Sản phẩm chưa có đánh giá được xử lý thế nào khi người mua lọc theo rating?

**V2 còn cần:** thống nhất tiêu chí kiểm duyệt và nguồn báo cáo/flag review hoặc listing.

## Slide 12 — Cách đo vận hành sau khi triển khai (đề xuất)

> Các chỉ số dưới đây là gợi ý để nhóm thống nhất; tài liệu dự án chưa quy định mục tiêu hay baseline số.

- **Khám phá:** tỷ lệ tìm kiếm không có kết quả; tỷ lệ mở listing từ trang kết quả; NDCG@5 baseline so với ML trên tập truy vấn gán nhãn.
- **Chuyển đổi:** tỷ lệ thêm giỏ → checkout thành công; tỷ lệ checkout thất bại do hết hàng hoặc thay đổi giá.
- **Vận hành shop:** thời gian từ nhận đơn đến cập nhật dispatch; tỷ lệ cập nhật tồn kho đúng hạn.
- **Tính toàn vẹn:** số giao dịch trùng (mục tiêu vận hành: 0); số sai lệch tổng payment mô phỏng so với tổng phân bổ.
- **Quyền riêng tư/chất lượng gợi ý:** xác nhận opt-out dừng ghi event và dùng history; tỷ lệ gợi ý bị loại do hết hàng/vượt budget.

**Ghi chú thuyết trình:** Nên đặt baseline trước khi đặt target. Với ML, theo dõi cả chỉ số xếp hạng ngoại tuyến lẫn hành vi người mua sau khi phát hành.

## Slide 13 — Kết luận

- Marketplace tổ chức khám phá sản phẩm và giao dịch cho nhiều cửa hàng trong một trải nghiệm chung.
- V1 tập trung vào luồng đầu-cuối: listing → tìm kiếm/gợi ý → giỏ đa shop → thanh toán mô phỏng → đơn theo shop → giao nhận.
- ML bổ trợ xếp hạng/gợi ý, đi kèm baseline, fallback, bộ lọc tồn kho/ngân sách và quyền tắt cá nhân hóa.
- Các quyết định về hủy đơn, hoàn tất đơn, rating sản phẩm chưa có đánh giá và kiểm duyệt cần được chốt để triển khai nhất quán.

**Câu kết:** “Mục tiêu của V1 là biến việc khám phá sản phẩm thành một giao dịch đa shop có thể kiểm soát, theo dõi và đối soát rõ ràng.”

## Tài liệu đã tổng hợp

- [README dự án](../README.md)
- [Use cases](Use_Cases.md)
- [Requirements](Requirements.md)
- [Specifications](Specifications.md)
- [Assumptions](Assumptions.md)
- [Risks](Risks.md)
- [Marketplace overview diagram](marketplace-overview.mmd)
- [Marketplace architecture diagram](marketplace-architecture.mmd)
- [Recommendation based on ML Algorithms (PDF)](Recommendation%20based%20on%20ML%20Algorithms.pdf)

