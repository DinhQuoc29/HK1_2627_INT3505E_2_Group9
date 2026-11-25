-- Danh mục ban đầu cho kênh người bán. Chạy lại không sửa danh mục đã có.
BEGIN;

INSERT INTO categories (id, name, slug, level)
VALUES
    (gen_random_uuid(), 'Điện tử', 'dien-tu', 1),
    (gen_random_uuid(), 'Thời trang', 'thoi-trang', 1),
    (gen_random_uuid(), 'Nhà cửa và đời sống', 'nha-cua-va-doi-song', 1),
    (gen_random_uuid(), 'Sách và văn phòng phẩm', 'sach-va-van-phong-pham', 1)
ON CONFLICT DO NOTHING;

INSERT INTO categories (id, parent_id, name, slug, level)
SELECT gen_random_uuid(), parent.id, leaf.name, leaf.slug, 2
FROM (VALUES
    ('dien-tu', 'Điện thoại và phụ kiện', 'dien-thoai-va-phu-kien'),
    ('dien-tu', 'Thiết bị âm thanh', 'thiet-bi-am-thanh'),
    ('dien-tu', 'Máy tính và phụ kiện', 'may-tinh-va-phu-kien'),
    ('thoi-trang', 'Quần áo', 'quan-ao'),
    ('thoi-trang', 'Giày dép', 'giay-dep'),
    ('thoi-trang', 'Túi và phụ kiện', 'tui-va-phu-kien'),
    ('nha-cua-va-doi-song', 'Đồ dùng nhà bếp', 'do-dung-nha-bep'),
    ('nha-cua-va-doi-song', 'Trang trí nhà cửa', 'trang-tri-nha-cua'),
    ('nha-cua-va-doi-song', 'Đồ gia dụng', 'do-gia-dung'),
    ('sach-va-van-phong-pham', 'Sách', 'sach'),
    ('sach-va-van-phong-pham', 'Dụng cụ học tập', 'dung-cu-hoc-tap'),
    ('sach-va-van-phong-pham', 'Văn phòng phẩm', 'van-phong-pham')
) AS leaf(parent_slug, name, slug)
JOIN categories AS parent ON parent.slug = leaf.parent_slug AND parent.level = 1
ON CONFLICT DO NOTHING;

COMMIT;
