from src.maintenance_messaging import decide_delivery


def test_undelivered_inspection_is_routed_to_tenant_contact() -> None:
    decision = decide_delivery("msg-7", {"status": "undelivered"})

    assert decision.action == "contact-tenant"
    assert decision.state == "undelivered"
