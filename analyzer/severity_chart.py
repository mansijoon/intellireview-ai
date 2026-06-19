def get_severity_chart_data(
    severities
):

    return {
        "Critical": severities["Critical"],
        "High": severities["High"],
        "Medium": severities["Medium"],
        "Low": severities["Low"]
    }
