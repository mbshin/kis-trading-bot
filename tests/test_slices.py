from __future__ import annotations
from kisbot.core.slices import SliceBook


def test_slicebook_basic_flow():
    book = SliceBook(equity=6000, slices_total=60)
    # Each slice is floor(6000/60)=100
    assert book.slice_value == 100
    assert book.slices_in_use == 0

    # Reserve 4 slices
    notional = book.reserve(4)
    assert notional == 400
    assert book.slices_in_use == 4

    # Cannot exceed total
    assert book.can_add(60) is False

    # Free resets usage
    book.free_all()
    assert book.slices_in_use == 0

