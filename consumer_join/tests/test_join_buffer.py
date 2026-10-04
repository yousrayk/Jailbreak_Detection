from app.join_buffer import JoinBuffer

MESSAGE = {"id": "id-1", "message": "hello"}
PREDICTION = {"id": "id-1", "classification": "benign", "confidence": 0.5, "model_version": "v1"}


def test_no_join_until_both_halves_present():
    buf = JoinBuffer()
    assert buf.add_message(MESSAGE) is None


def test_join_emits_when_prediction_arrives_after_message():
    buf = JoinBuffer()
    buf.add_message(MESSAGE)
    joined = buf.add_prediction(PREDICTION)
    assert joined == {
        "id": "id-1",
        "message": "hello",
        "classification": "benign",
        "confidence": 0.5,
        "model_version": "v1",
    }


def test_join_emits_when_message_arrives_after_prediction():
    buf = JoinBuffer()
    buf.add_prediction(PREDICTION)
    joined = buf.add_message(MESSAGE)
    assert joined is not None
    assert joined["classification"] == "benign"


def test_buffer_clears_after_join_so_it_does_not_rejoin_on_duplicate():
    buf = JoinBuffer()
    buf.add_message(MESSAGE)
    first = buf.add_prediction(PREDICTION)
    assert first is not None

    # A duplicate prediction delivery (at-least-once) shouldn't rejoin
    # without a fresh message for the same id.
    second = buf.add_prediction(PREDICTION)
    assert second is None


def test_different_ids_do_not_cross_join():
    buf = JoinBuffer()
    buf.add_message({"id": "id-1", "message": "one"})
    buf.add_message({"id": "id-2", "message": "two"})
    joined = buf.add_prediction({"id": "id-2", "classification": "jailbreak", "confidence": 0.99, "model_version": "v1"})
    assert joined["message"] == "two"
