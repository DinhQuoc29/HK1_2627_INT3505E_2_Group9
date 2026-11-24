def product(pid, slot='women_bags', price=100, available=True, text='túi dự tiệc thanh lịch'):
    return {'id': str(pid), 'name': text, 'description': text, 'text': text,
            'slot': slot, 'brand': 'Demo', 'price': price, 'available': available,
            'inventory_status': 'available' if available else 'out_of_stock',
            'image_url': 'https://example.com/image.jpg', 'rating': None, 'review_count': None}


def raw_product(pid, slot='women_bags', price=100, available=True):
    return {'productId': pid, 'name': 'Túi dự tiệc', 'description': 'Túi đựng đồ dùng khi đi dự tiệc.',
            'collectionGroup': slot, 'price': price, 'currency': 'VND',
            'inventoryStatus': 'available' if available else 'out_of_stock',
            'thumbnailUrl': 'https://example.com/image.jpg'}
