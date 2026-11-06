def test_vyapaar_data_import():
    import vyapaar_data

    assert vyapaar_data.__version__ == "0.1.0"
    assert vyapaar_data.VyapaarDataService is not None
