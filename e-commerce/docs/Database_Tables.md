# Database Tables

## **Data dictionary**

### **Auth**

#### **users**

Tài khoản người dùng, role và trạng thái khóa đăng nhập. **Mức:** P0. **REQ:** AUTH-1, AUTH-3.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | AUTH-1 |
| email | VARCHAR(255) | không |  | UNIQUE | Email đăng nhập, lưu chữ thường | AUTH-1 |
| password\_hash | VARCHAR(100) | có |  |  | BCrypt hash; NULL nếu tài khoản chỉ đăng nhập Google | AUTH-1, NFR bảo mật |
| full\_name | VARCHAR(100) | không |  |  | Tên hiển thị | AUTH-1 |
| role | TEXT | không | 'buyer' | CHECK (role IN ('buyer','seller','admin')) | Một role mỗi user; admin chỉ cấp qua luồng quản trị | AUTH-3 |
| failed\_login\_count | SMALLINT | không | 0 | CHECK (failed\_login\_count \>= 0\) | Số lần đăng nhập sai liên tiếp, về 0 khi đăng nhập đúng | AUTH-1 (RISK chiếm đoạt) |
| locked\_until | TIMESTAMPTZ | có |  |  | Khóa đăng nhập tạm thời đến thời điểm này | AUTH-1 (RISK chiếm đoạt) |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

> * ck\_users\_email\_lower CHECK (email \= lower(email))

#### **user\_identities**

Liên kết tài khoản với nhà cung cấp OAuth (Google, Facebook). **Mức:** P1. **REQ:** ĐB-OAUTH.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | ĐB-OAUTH |
| user\_id | UUID | không |  | FK → users.id (CASCADE) | Tài khoản được liên kết | ĐB-OAUTH |
| provider | TEXT | không |  | CHECK (provider IN ('google','facebook')) | Nhà cung cấp OAuth: google, facebook (migration 002) | ĐB-OAUTH |
| provider\_subject | VARCHAR(255) | không |  |  | Google: claim \`sub\`; Facebook: \`id\` của người dùng (định danh ổn định, không dùng email) | ĐB-OAUTH |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |

> * uq\_user\_identities\_provider\_subject UNIQUE (provider, provider\_subject)  
> * uq\_user\_identities\_user\_provider UNIQUE (user\_id, provider)

#### **auth\_sessions**

Phiên đăng nhập: refresh token (hash) và trạng thái thu hồi; id \= claim \`sid\` trong access JWT. **Mức:** P0. **REQ:** AUTH-2.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7; chính là claim \`sid\` trong access token | AUTH-2 |
| user\_id | UUID | không |  | FK → users.id (CASCADE) | Chủ phiên | AUTH-2 |
| refresh\_token\_hash | CHAR(64) | không |  | UNIQUE | SHA-256 (hex) của refresh token; không lưu token gốc | AUTH-2 |
| expires\_at | TIMESTAMPTZ | không |  |  | Hết hạn refresh token | AUTH-2 |
| revoked\_at | TIMESTAMPTZ | có |  |  | Thời điểm logout/thu hồi; khác NULL thì mọi token của phiên bị từ chối | AUTH-2 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

### **Catalog**

#### **provinces**

Bảng tra cứu tỉnh/thành (34 đơn vị sau sáp nhập 07/2025), seed bằng migration. **Mức:** P1. **REQ:** SRCH-2.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| code | VARCHAR(4) | không |  | PK | Mã tỉnh, dùng làm khóa tự nhiên | SRCH-2 |
| name | VARCHAR(100) | không |  | UNIQUE | Tên tỉnh/thành | SRCH-2 |

#### **shops**

Shop của seller (1 seller : 1 shop); nơi bán \= tỉnh của shop. **Mức:** P0. **REQ:** AUTH-4, CART-3, ORD-3, ORD-6, SRCH-2.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | AUTH-4 |
| owner\_user\_id | UUID | không |  | UNIQUE; FK → users.id (RESTRICT) | Seller sở hữu; UNIQUE đảm bảo 1 seller 1 shop |   |
| name | VARCHAR(150) | không |  |  | Tên shop | CAT-2 |
| province\_code | VARCHAR(4) | không |  | FK → provinces.code (RESTRICT) | Nơi bán, dùng cho bộ lọc tỉnh | SRCH-2 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

#### **categories**

Danh mục 2 cấp (cha-con); sản phẩm chỉ gắn vào danh mục cấp 2 (lá). **Mức:** P0. **REQ:** CAT-1, SRCH-1, ĐB-NEW20.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | CAT-1 |
| parent\_id | UUID | có |  | FK → categories.id (RESTRICT) | Danh mục cha; NULL nếu là cấp 1 | CAT-1 |
| name | VARCHAR(100) | không |  |  | Tên danh mục | CAT-1 |
| slug | VARCHAR(120) | không |  | UNIQUE | Định danh dạng chữ cho URL | CAT-1 |
| level | SMALLINT | không |  | CHECK (level IN (1, 2)) | 1 \= cha, 2 \= con (lá) | CAT-1 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

> * ck\_categories\_level\_parent CHECK ((parent\_id IS NULL) \= (level \= 1))  
> * uq\_categories\_parent\_name UNIQUE NULLS NOT DISTINCT (parent\_id, name)

#### **products**

Sản phẩm đang bán; ngừng bán bằng status thay vì xóa. **Mức:** P0. **REQ:** CAT-1, CAT-2, SRCH-1, SRCH-2.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | CAT-1 |
| shop\_id | UUID | không |  | FK → shops.id (RESTRICT) | Shop sở hữu | CAT-2, ORD-3 |
| category\_id | UUID | không |  | FK → categories.id (RESTRICT) | Danh mục lá (cấp 2), kiểm tra ở service | CAT-1, SRCH-1 |
| brand | VARCHAR(100) | có |  |  | Tên thương hiệu dùng để lọc sản phẩm, NULL nếu không có | SRCH-2 |
| name | VARCHAR(255) | không |  |  | Tên sản phẩm | CAT-1 |
| name\_normalized | VARCHAR(255) | không |  |  | Tên chữ thường, bỏ dấu (app tính khi ghi); dùng cho tìm kiếm trigram | SRCH-1 |
| description | TEXT | có |  |  | Mô tả | CAT-1 |
| price | BIGINT | không |  | CHECK (price \> 0\) | Giá hiện tại, VND (số nguyên) | CAT-2, REC-2 |
| status | TEXT | không | 'active' | CHECK (status IN ('active','inactive')) | inactive \= ngừng bán; chặn đặt hàng, ẩn khỏi tìm kiếm và gợi ý | CAT-2 (chặn đặt sp ngừng bán) |
| rating\_avg | NUMERIC(3,2) | không | 0 | CHECK (rating\_avg BETWEEN 0 AND 5\) | Điểm TB các review visible; Reviews cập nhật qua catalog.service | SRCH-2, POP-1 |
| rating\_count | INTEGER | không | 0 | CHECK (rating\_count \>= 0\) | Số review visible | SRCH-2, POP-1 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

#### **product\_images**

Ảnh sản phẩm (URL); ảnh position 0 là ảnh đại diện. **Mức:** P1. **REQ:** CAT-1.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | CAT-1 |
| product\_id | UUID | không |  | FK → products.id (CASCADE) | Sản phẩm | CAT-1 |
| url | VARCHAR(500) | không |  |  | URL ảnh | CAT-1 |
| position | SMALLINT | không | 0 | CHECK (position \>= 0\) | Thứ tự hiển thị | CAT-1 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |

> * uq\_product\_images\_product\_position UNIQUE (product\_id, position)

### **Cart**

#### **cart\_items**

Giỏ hàng theo tài khoản; một dòng cho mỗi (user, product). **Mức:** P0. **REQ:** CART-1, CART-2, CART-3.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| user\_id | UUID | không |  | FK → users.id (CASCADE) | Chủ giỏ | CART-1 |
| product\_id | UUID | không |  | FK → products.id (CASCADE) | Sản phẩm trong giỏ | CART-1 |
| quantity | INTEGER | không |  | CHECK (quantity \> 0\) | Số lượng nguyên dương | CART-2 |
| unit\_price\_at\_add | BIGINT | không |  | CHECK (unit\_price\_at\_add \> 0\) | Giá lúc thêm; so với giá hiện tại để báo đổi giá | CART-2 (RISK giá cũ) |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

> * pk\_cart\_items PRIMARY KEY (user\_id, product\_id)

### **Order & Inventory**

#### **inventories**

Tồn kho, 1-1 với product; chưa có dòng \= tồn 0\. **Mức:** P0. **REQ:** ORD-1, ORD-2.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| product\_id | UUID | không |  | PK; FK → products.id (CASCADE) | Sản phẩm | ORD-1 |
| quantity | INTEGER | không | 0 | CHECK (quantity \>= 0\) | Tồn hiện tại; CHECK là chốt chặn cuối chống tồn âm | ORD-2 |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

#### **checkouts**

Một lượt xác nhận mua; gom các order tách theo shop; chống trùng bằng idempotency key. **Mức:** P0. **REQ:** ORD-2, ORD-3.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | ORD-3 |
| buyer\_id | UUID | không |  | FK → users.id (RESTRICT) | Người mua | ORD-5 |
| idempotency\_key | VARCHAR(64) | không |  |  | Header Idempotency-Key của POST /checkouts | ORD-3 (SPEC chống trùng) |
| request\_hash | CHAR(64) | không |  |  | SHA-256 body đã chuẩn hóa; cùng key khác body → 409 | ORD-3 |
| total\_amount | BIGINT | không |  | CHECK (total\_amount \>= 0\) | Tổng tiền lúc đặt (bất biến), VND | PAY-1 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |

> * uq\_checkouts\_buyer\_key UNIQUE (buyer\_id, idempotency\_key)

#### **orders**

Đơn của một shop trong một lượt mua; có state machine. **Mức:** P0. **REQ:** ORD-3, ORD-4, ORD-5, ORD-6.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | ORD-4 |
| checkout\_id | UUID | không |  | FK → checkouts.id (RESTRICT) | Lượt mua chứa đơn | ORD-3 |
| buyer\_id | UUID | không |  | FK → users.id (RESTRICT) | Khi tạo đơn, service lấy buyer\_id từ checkout của đơn để lọc quyền và lịch sử đơn | ORD-5, AUTH-4 |
| shop\_id | UUID | không |  | FK → shops.id (RESTRICT) | Shop xử lý đơn | ORD-6, AUTH-4 |
| status | TEXT | không | 'pending\_payment' | CHECK (status IN ('pending\_payment','paid','shipping','completed','cancelled')) | Trạng thái theo state machine (thẻ Nghiệp vụ) | ORD-4, ORD-6 |
| total\_amount | BIGINT | không |  | CHECK (total\_amount \>= 0\) | Tổng các order\_items, VND | PAY-1 |
| shipping\_name | VARCHAR(100) | không |  |  | Snapshot tên người nhận | ORD-6 (ASM giao nhận) |
| shipping\_phone | VARCHAR(20) | không |  |  | Snapshot SĐT người nhận | ORD-6 |
| shipping\_address | VARCHAR(500) | không |  |  | Snapshot địa chỉ (text) | ORD-6 |
| paid\_at | TIMESTAMPTZ | có |  |  | Thời điểm thanh toán thành công | PAY-1 |
| shipped\_at | TIMESTAMPTZ | có |  |  | Seller chuyển sang shipping | ORD-6 |
| completed\_at | TIMESTAMPTZ | có |  |  | Seller xác nhận giao xong; mở quyền review | ORD-6, REV-1 |
| cancelled\_at | TIMESTAMPTZ | có |  |  | Thời điểm hủy | ORD-4 |
| cancelled\_by | TEXT | có |  | CHECK (cancelled\_by IN ('buyer','seller')) | Ai hủy | ORD-4 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

> * uq\_orders\_checkout\_shop UNIQUE (checkout\_id, shop\_id)  
> * ck\_orders\_cancel\_fields CHECK ((status = 'cancelled' AND cancelled\_at IS NOT NULL AND cancelled\_by IS NOT NULL) OR (status <> 'cancelled' AND cancelled\_at IS NULL AND cancelled\_by IS NULL))  
> * ck\_orders\_paid\_at CHECK (status NOT IN ('paid','shipping','completed') OR paid\_at IS NOT NULL)  
> * ck\_orders\_shipped\_at CHECK (status NOT IN ('shipping','completed') OR shipped\_at IS NOT NULL)  
> * ck\_orders\_completed\_at CHECK ((status \= 'completed') \= (completed\_at IS NOT NULL))

#### **order\_items**

Dòng hàng của đơn, lưu snapshot tên/giá/số lượng. **Mức:** P0. **REQ:** ORD-3, CAT (giữ thông tin đơn cũ).

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | ORD-3 |
| order\_id | UUID | không |  | FK → orders.id (CASCADE) | Đơn chứa dòng | ORD-3 |
| product\_id | UUID | không |  | FK → products.id (RESTRICT) | Sản phẩm; RESTRICT nên product đã có đơn không xóa được | CAT-2 |
| product\_name | VARCHAR(255) | không |  |  | Snapshot tên lúc đặt | CAT (giữ thông tin đơn cũ) |
| unit\_price | BIGINT | không |  | CHECK (unit\_price \> 0\) | Snapshot đơn giá lúc đặt, VND | CAT, CART (backend tự tính tiền) |
| quantity | INTEGER | không |  | CHECK (quantity \> 0\) | Số lượng | ORD-1 |
| line\_total | BIGINT | không |  |  | unit\_price × quantity | PAY-1 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |

> * ck\_order\_items\_line\_total CHECK (line\_total \= unit\_price \* quantity)  
> * uq\_order\_items\_order\_product UNIQUE (order\_id, product\_id)

### **Payment**

#### **payments**

Một payment giả lập cho mỗi lượt mua; UNIQUE(checkout\_id) chống thanh toán trùng. **Mức:** P0. **REQ:** PAY-1, PAY-2.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | PAY-1 |
| checkout\_id | UUID | không |  | UNIQUE; FK → checkouts.id (RESTRICT) | Lượt mua; UNIQUE \= một payment mỗi lượt mua | PAY-2 |
| buyer\_id | UUID | không |  | FK → users.id (RESTRICT) | Khi tạo payment, service lấy buyer\_id từ checkout của payment để kiểm tra quyền xem | AUTH-4 |
| method | TEXT | không | 'simulated' | CHECK (method IN ('simulated')) | v1 chỉ có giả lập; API hiển thị rõ là demo | PAY (ASM giả lập) |
| status | TEXT | không | 'pending' | CHECK (status IN ('pending','succeeded','failed','cancelled')) | State machine payment (thẻ Nghiệp vụ) | PAY-1 |
| amount | BIGINT | không | 0 | CHECK (amount \>= 0\) | Số tiền đã thu \= tổng order còn chờ thanh toán lúc thành công; 0 khi chưa thu | PAY-1 |
| refunded\_amount | BIGINT | không | 0 |  | Tổng tiền hoàn (giả lập) do hủy đơn đã trả | PAY (hủy đơn cập nhật tiền) |
| attempt\_count | SMALLINT | không | 0 | CHECK (attempt\_count \>= 0\) | Số lần thử thanh toán | PAY-1 |
| paid\_at | TIMESTAMPTZ | có |  |  | Thời điểm thành công | PAY-1 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

> * ck\_payments\_refund\_range CHECK (refunded\_amount BETWEEN 0 AND amount)  
> * ck\_payments\_paid\_at CHECK ((status \= 'succeeded') \= (paid\_at IS NOT NULL))

#### **payment\_allocations**

Phân bổ tiền của payment cho từng order; đánh dấu hoàn tiền khi hủy. **Mức:** P0. **REQ:** PAY-1 (SPEC lưu phân bổ theo đơn).

Khi tạo phân bổ, service kiểm tra payment và order có cùng checkout\_id. Nếu hai giá trị khác nhau, service từ chối phân bổ kể cả khi hai lượt mua thuộc cùng một người.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | PAY-1 |
| payment\_id | UUID | không |  | FK → payments.id (RESTRICT) | Payment | PAY-1 |
| order\_id | UUID | không |  | UNIQUE; FK → orders.id (RESTRICT) | Order được phân bổ; UNIQUE \= mỗi order thu tiền một lần | PAY-2 |
| amount | BIGINT | không |  | CHECK (amount \>= 0\) | \= orders.total\_amount lúc thu | PAY-1 |
| status | TEXT | không | 'captured' | CHECK (status IN ('captured','refunded')) | refunded khi order bị hủy sau thanh toán | ORD-4 |
| refunded\_at | TIMESTAMPTZ | có |  |  | Thời điểm hoàn | ORD-4 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |

> * ck\_payment\_allocations\_refund CHECK ((status \= 'refunded') \= (refunded\_at IS NOT NULL))

### **Reviews**

#### **reviews**

Đánh giá sản phẩm đã mua; một review cho mỗi order\_item của đơn completed. **Mức:** P1 (nâng từ P2). **REQ:** REV-1, SRCH-2, POP-1.

Khi tạo đánh giá, service tra đơn hàng từ order\_item\_id. Chỉ cho phép ghi khi đơn có trạng thái completed và buyer\_id của đơn là ID người đang đăng nhập. Service lấy product\_id từ dòng hàng và user\_id từ phiên đăng nhập.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| id | UUID | không |  | PK | UUIDv7 sinh ở app; dùng làm id công khai | REV-1 |
| order\_item\_id | UUID | không |  | UNIQUE; FK → order\_items.id (RESTRICT) | Dòng hàng đã mua; UNIQUE chống đánh giá trùng | REV-1 (giới hạn theo order item) |
| product\_id | UUID | không |  | FK → products.id (RESTRICT) | Lặp từ order\_item để liệt kê review theo sản phẩm | REV-1 |
| user\_id | UUID | không |  | FK → users.id (RESTRICT) | Tác giả; chỉ tác giả/admin được sửa xóa | REV-1 |
| rating | SMALLINT | không |  | CHECK (rating BETWEEN 1 AND 5\) | Số sao 1–5 | REV-1 |
| content | TEXT | có |  | CHECK (char\_length(content) \<= 2000\) | Nội dung, tối đa 2000 ký tự | REV-1 (giới hạn đầu vào) |
| status | TEXT | không | 'visible' | CHECK (status IN ('visible','hidden')) | hidden \= admin ẩn nội dung không phù hợp; không tính vào rating | REV-1 |
| created\_at | TIMESTAMPTZ | không | now() |  | Thời điểm tạo (UTC) |  |
| updated\_at | TIMESTAMPTZ | không | now() |  | Thời điểm sửa gần nhất (ORM onupdate) |  |

### **Privacy**

#### **privacy_settings**

Tùy chọn cá nhân hóa gắn với tài khoản; tạo khi đăng ký. **Mức:** P1. **REQ:** PRV-1.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| user\_id | UUID | không |   | PK; FK → users.id (CASCADE) | Tài khoản | PRV-1 |
| personalization\_enabled | BOOLEAN | không | TRUE |   | FALSE: không ghi event hành vi, không dùng lịch sử để gợi ý | PRV-1 |
| updated\_at | TIMESTAMPTZ | không | now() |   | Thời điểm sửa gần nhất (ORM onupdate) |   |

### **Behavior Events**

#### **behavior_events**

Log hành vi chỉ ghi thêm (append-only); không FK sang OLTP. **Mức:** P1. **REQ:** EVT-1, EVT-2, ĐB-EVT10.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| id | BIGINT | không |   | PK; identity | Khóa nội bộ, không lộ ra API | EVT-1 |
| client\_event\_id | UUID | không |   | UNIQUE | Mã event do client (hoặc server) sinh; chống trùng | EVT-1 (chống trùng theo mã event) |
| event\_type | TEXT | không |   | CHECK (event\_type IN ('click','product\_view','search','filter','impression','view\_review','add\_to\_cart','remove\_from\_cart','purchase')) | Loại event; repeat\_purchase = purchase có is\_repeat = TRUE | ĐB-EVT10 |
| user\_id | UUID | có |   |   | NULL nếu khách chưa đăng nhập | EVT-1 |
| session\_id | UUID | không |   |   | UUID ngẫu nhiên do FE sinh (header X-Session-Id); không phải fingerprint | EVT-1 |
| product\_id | UUID | có |   |   | Sản phẩm liên quan | EVT-1 |
| category\_id | UUID | có |   |   | Danh mục (filter/category view) | ĐB-EVT10 |
| order\_id | UUID | có |   |   | Đơn (purchase) | ĐB-EVT10 |
| rec\_request\_id | UUID | có |   |   | Mã lượt gợi ý sinh ra impression/click | EVT-2 (gắn với mã lượt gợi ý) |
| search\_event\_id | UUID | có |   |   | client\_event\_id của event search dẫn tới click này | ĐB-EVT10 (sp bấm sau khi tìm) |
| placement | TEXT | có |   | CHECK (placement IN ('home','similar','popular','new\_user','search','category','cart','product\_detail','other')) | Khối hiển thị nơi xảy ra impression/click | EVT-2 (CTR) |
| position | SMALLINT | có |   | CHECK (position \>= 0) | Vị trí trong danh sách | EVT-2 |
| search\_query | VARCHAR(200) | có |   |   | Từ khóa (search) | ĐB-EVT10 |
| filters | JSONB | có |   |   | Bộ lọc đã chọn (giá, thương hiệu, tỉnh, sao) | ĐB-EVT10 |
| dwell\_ms | INTEGER | có |   | CHECK (dwell\_ms \>= 0) | Thời gian ở trang chi tiết (product\_view) | ĐB-EVT10 |
| quantity | INTEGER | có |   | CHECK (quantity \> 0) | Số lượng (cart, purchase) | ĐB-EVT10 |
| unit\_price | BIGINT | có |   | CHECK (unit\_price \> 0) | Đơn giá (cart, purchase) | ĐB-EVT10 |
| is\_repeat | BOOLEAN | có |   |   | purchase: buyer đã từng mua sản phẩm này | ĐB-EVT10 (repeat\_purchase) |
| occurred\_at | TIMESTAMPTZ | không |   |   | Thời điểm xảy ra (client) hoặc commit (server) | EVT-1 |
| received\_at | TIMESTAMPTZ | không | now() |   | Thời điểm server nhận | EVT-1 |

> * ck\_events\_product\_required CHECK (event\_type NOT IN ('click','product\_view','impression','view\_review','add\_to\_cart','remove\_from\_cart','purchase') OR product\_id IS NOT NULL)  
> * ck\_events\_search CHECK (event\_type \<\> 'search' OR search\_query IS NOT NULL)  
> * ck\_events\_filter CHECK (event\_type \<\> 'filter' OR category\_id IS NOT NULL OR filters IS NOT NULL)  
> * ck\_events\_cart CHECK (event\_type NOT IN ('add\_to\_cart','remove\_from\_cart') OR (quantity IS NOT NULL AND user\_id IS NOT NULL))  
> * ck\_events\_purchase CHECK (event\_type \<\> 'purchase' OR (order\_id IS NOT NULL AND user\_id IS NOT NULL AND quantity IS NOT NULL AND unit\_price IS NOT NULL AND is\_repeat IS NOT NULL))  
> * ck\_events\_dwell CHECK (dwell\_ms IS NULL OR event\_type = 'product\_view')  

### **Popular & Fallback**

#### **product_daily_stats**

Số liệu theo ngày (UTC) cho từng sản phẩm; job upsert. **Mức:** P1. **REQ:** POP-1.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| product\_id | UUID | không |   |   | Sản phẩm | POP-1 |
| stat\_date | DATE | không |   |   | Ngày (UTC) | POP-1 |
| view\_count | INTEGER | không | 0 |   | Số product\_view | POP-1 (view) |
| unique\_viewers | INTEGER | không | 0 |   | Số người xem khác nhau trong ngày (user\_id, hoặc session\_id nếu là khách) | POP-1 (giảm tương tác lặp) |
| click\_count | INTEGER | không | 0 |   | Số click | POP-1 (click) |
| add\_to\_cart\_count | INTEGER | không | 0 |   | Số add\_to\_cart | POP-1 (add-to-cart) |
| order\_count | INTEGER | không | 0 |   | Số đơn hợp lệ (paid/shipping/completed) chứa sản phẩm, theo ngày paid\_at | POP-1 (chỉ tính giao dịch hợp lệ) |
| units\_sold | INTEGER | không | 0 |   | Số lượng bán trong các đơn đó | POP-1 (số lượng bán) |
| updated\_at | TIMESTAMPTZ | không | now() |   | Thời điểm sửa gần nhất (ORM onupdate) |   |

> * pk\_product\_daily\_stats PRIMARY KEY (product\_id, stat\_date)  
> * ck\_product\_daily\_stats\_nonneg CHECK (view\_count \>= 0 AND unique\_viewers \>= 0 AND click\_count \>= 0 AND add\_to\_cart\_count \>= 0 AND order\_count \>= 0 AND units\_sold \>= 0)  

#### **product_popularity**

Chỉ số phổ biến 30 ngày và điểm có time decay; danh sách tính trước cho tab Phổ biến, người mới, fallback; đồng thời là feature sản phẩm cho ML. **Mức:** P1. **REQ:** POP-1, POP-2, ĐB-NEW20.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| product\_id | UUID | không |   | PK | Sản phẩm | POP-1 |
| views\_30d | INTEGER | không | 0 |   | Tổng view 30 ngày | POP-1 |
| unique\_viewers\_30d | INTEGER | không | 0 |   | Tổng unique viewers theo ngày (cộng dồn) | POP-1 |
| clicks\_30d | INTEGER | không | 0 |   | Tổng click | POP-1 |
| add\_to\_cart\_30d | INTEGER | không | 0 |   | Tổng add-to-cart | POP-1 |
| orders\_30d | INTEGER | không | 0 |   | Tổng đơn hợp lệ | POP-1 |
| units\_sold\_30d | INTEGER | không | 0 |   | Tổng số lượng bán | POP-1 |
| add\_to\_cart\_rate | DOUBLE PRECISION | không | 0 |   | add\_to\_cart\_30d / max(views\_30d, 1) | POP-1 |
| conversion\_rate | DOUBLE PRECISION | không | 0 |   | orders\_30d / max(views\_30d, 1) | POP-1 |
| rating\_avg | NUMERIC(3,2) | không | 0 |   | Snapshot từ products lúc tính | POP-1 |
| rating\_count | INTEGER | không | 0 |   | Snapshot từ products lúc tính | POP-1 |
| score | DOUBLE PRECISION | không |   |   | Điểm phổ biến có time decay (công thức ở thẻ Nghiệp vụ) | POP-1 (time decay) |
| computed\_at | TIMESTAMPTZ | không |   |   | Lần tính gần nhất | POP-2 |

### **Recommendation & Budget**

#### **user_recommendations**

Top-K ứng viên mỗi user do pipeline offline tính sẵn; API lọc ngân sách/tồn kho lúc trả. **Mức:** P1. **REQ:** REC-1, Q02.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| user\_id | UUID | không |   |   | User | REC-1 |
| product\_id | UUID | không |   |   | Sản phẩm ứng viên | REC-1 |
| rank | SMALLINT | không |   | CHECK (rank \>= 1) | Thứ hạng do model xếp | REC-1 |
| score | DOUBLE PRECISION | không |   |   | Điểm model | REC-1 |
| model\_version | VARCHAR(50) | không |   |   | Phiên bản model sinh kết quả | Q06 |
| generated\_at | TIMESTAMPTZ | không |   |   | Thời điểm batch chạy; quá cũ → fallback stale\_model | POP-2 |

> * pk\_user\_recommendations PRIMARY KEY (user\_id, product\_id)  
> * uq\_user\_recommendations\_rank UNIQUE (user\_id, rank)  

#### **product_similarities**

Danh sách 'Sản phẩm tương tự' tính sẵn; không cá nhân hóa. **Mức:** P1. **REQ:** ĐB-SIM.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| product\_id | UUID | không |   |   | Sản phẩm gốc | ĐB-SIM |
| similar\_product\_id | UUID | không |   |   | Sản phẩm tương tự | ĐB-SIM |
| rank | SMALLINT | không |   | CHECK (rank \>= 1) | Thứ hạng | ĐB-SIM |
| score | DOUBLE PRECISION | không |   |   | Độ tương tự | ĐB-SIM |
| model\_version | VARCHAR(50) | không |   |   | Phiên bản model | Q06 |
| generated\_at | TIMESTAMPTZ | không |   |   | Thời điểm batch chạy | ĐB-SIM |

> * pk\_product\_similarities PRIMARY KEY (product\_id, similar\_product\_id)  
> * uq\_product\_similarities\_rank UNIQUE (product\_id, rank)  
> * ck\_product\_similarities\_self CHECK (product\_id \<\> similar\_product\_id)  

#### **recommendation_requests**

Log mỗi lượt trả gợi ý/phổ biến: nguồn model hay popular, lý do fallback, độ trễ; id gắn vào impression/click. **Mức:** P1. **REQ:** EVT-2, Q04, Q05.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| id | UUID | không |   | PK | UUIDv7 = rec\_request\_id trả cho FE | EVT-2 |
| user\_id | UUID | có |   |   | NULL nếu khách | EVT-2 |
| session\_id | UUID | có |   |   | Phiên FE | EVT-2 |
| placement | TEXT | không |   | CHECK (placement IN ('home','similar','popular','new\_user')) | Khối gợi ý | EVT-2 |
| context\_product\_id | UUID | có |   |   | Sản phẩm gốc (placement = similar) | ĐB-SIM |
| max\_price | BIGINT | có |   | CHECK (max\_price \> 0) | Ngân sách user nhập (trần giá mỗi sản phẩm) | REC-2, Q04 |
| source | TEXT | không |   | CHECK (source IN ('model','popular')) | Kết quả lấy từ model hay danh sách phổ biến | Q05 (ghi nguồn kết quả) |
| fallback\_reason | TEXT | có |   | CHECK (fallback\_reason IN ('cold\_start','personalization\_off','guest','model\_error','timeout','stale\_model')) | Lý do dùng popular thay model (chỉ với home/similar) | POP-2, Q05 |
| model\_version | VARCHAR(50) | có |   |   | Phiên bản model (khi source = model) | Q03, Q06 |
| requested\_count | SMALLINT | không |   | CHECK (requested\_count \> 0) | Số sản phẩm yêu cầu | REC (thiếu ứng viên trả ít hơn) |
| returned\_count | SMALLINT | không |   | CHECK (returned\_count \>= 0) | Số sản phẩm thực trả | Q04 (tỷ lệ có kết quả) |
| latency\_ms | INTEGER | không |   | CHECK (latency\_ms \>= 0) | Độ trễ xử lý | Q02 |
| created\_at | TIMESTAMPTZ | không | now() |   | Thời điểm tạo (UTC) |   |

> * ck\_rec\_requests\_fallback CHECK (fallback\_reason IS NULL OR source = 'popular')  

#### **recommendation_items**

Các sản phẩm đã trả trong một lượt gợi ý, kèm giá tại thời điểm trả. **Mức:** P1. **REQ:** Q04, EVT-2.

| Cột | Kiểu | Null | Default | Khóa/ràng buộc | Mô tả | REQ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| request\_id | UUID | không |   | FK → recommendation\_requests.id (CASCADE) | Lượt gợi ý (FK cùng module; xóa log cũ thì xóa theo) | EVT-2 |
| rank | SMALLINT | không |   | CHECK (rank \>= 1) | Vị trí hiển thị | EVT-2 |
| product\_id | UUID | không |   |   | Sản phẩm | EVT-2 |
| score | DOUBLE PRECISION | có |   |   | Điểm model hoặc điểm popular | Q03 |
| price\_at\_time | BIGINT | không |   | CHECK (price\_at\_time \> 0) | Giá lúc trả; dùng đo Budget Violation Rate | Q04 (ghi thời điểm giá) |

> * pk\_recommendation\_items PRIMARY KEY (request\_id, rank)  
