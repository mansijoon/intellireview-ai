import streamlit as st

from analyzer.review_engine import review_code
from analyzer.code_metrics import calculate_metrics

from analyzer.review_parser import (
    extract_score,
    extract_security,
    extract_performance,
    extract_code_smells
)

from analyzer.repository_analyzer import (
    extract_repository,
    collect_source_code
)

from analyzer.repository_metrics import (
    repository_metrics
)

from analyzer.pdf_generator import (
    generate_pdf
)

from analyzer.severity_parser import (
    extract_severity_counts
)

from analyzer.file_explorer import (
    get_repository_files
)

from analyzer.repository_summary import (
    generate_repository_summary
)


from analyzer.repository_health import (
    calculate_repository_health
)

from analyzer.chart_data import (
    get_repository_chart_data
)

import pandas as pd

from analyzer.severity_chart import (
    get_severity_chart_data
)

from analyzer.github_analyzer import (
    clone_repository
)

from analyzer.repository_reviewer import (
    review_repository
)

from analyzer.repository_summary_ai import (
    generate_repository_ai_summary
)

from analyzer.static_analysis import (
    run_static_analysis
)

from analyzer.static_report import (
    format_static_findings
)

from analyzer.static_score import (
    calculate_static_score
)

from analyzer.repository_static_analysis import (
    analyze_repository_static
)

from analyzer.security_score import (
    calculate_security_score
)

from analyzer.security_summary import (
    summarize_security_findings
)

from analyzer.repository_risk_ranking import (
    rank_repository_files
)

from analyzer.executive_summary import (
    generate_executive_summary
)

from analyzer.repository_executive_summary import (
    generate_repository_executive_summary
)

from analyzer.fix_suggester import (
    generate_fix_suggestions
)

from analyzer.ai_fix_suggester import (
    generate_ai_fix_suggestions
)

from analyzer.architecture_analyzer import (
    analyze_repository_architecture
)

from analyzer.architecture_score import (
    calculate_architecture_score
)

from analyzer.pr_review import (
    review_pull_request
)

from analyzer.historical_comparison import (
    compare_versions
)

from analyzer.history_store import (
    get_previous_score
)

architecture_findings = []
architecture_score = 100

st.set_page_config(
    page_title="IntelliReview AI",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 IntelliReview AI")

st.subheader(
    "AI-Powered Code Review System"
)

analysis_mode = st.radio(
    "Analysis Mode",
    [
        "Single File",
        "Repository ZIP",
        "GitHub Repository",
        "Pull Request Review"
    ]
)

if analysis_mode == "Single File":

    uploaded_file = st.file_uploader(
        "Upload Source Code",
        type=["py", "java", "cpp", "js"]
    )

elif analysis_mode == "Repository ZIP":

    uploaded_file = st.file_uploader(
        "Upload Repository ZIP",
        type=["zip"]
    )

elif analysis_mode == "GitHub Repository":

    repo_url = st.text_input(
        "GitHub Repository URL"
    )

    uploaded_file = None

else:

    pr_diff = st.text_area(
        "Paste Pull Request Diff",
        height=300
    )

    uploaded_file = None

if (
    uploaded_file
    or
    (
        analysis_mode == "GitHub Repository"
        and repo_url
    )
    or
    (
        analysis_mode == "Pull Request Review"
        and pr_diff
    )
):

    if analysis_mode == "Single File":

        code = uploaded_file.read().decode(
            "utf-8"
        )

    elif analysis_mode == "Pull Request Review":

        code = pr_diff

    elif analysis_mode == "Repository ZIP":

        zip_path = "uploads/repository.zip"

        with open(
            zip_path,
            "wb"
        ) as f:

            f.write(
                uploaded_file.getbuffer()
            )

        extract_repository(
            zip_path,
            "uploads/extracted_repo"
        )

        repo_path = "uploads/extracted_repo"

    elif analysis_mode == "GitHub Repository":

        repo_path = clone_repository(
            repo_url
        )
        
    if analysis_mode in (
        "Repository ZIP",
        "GitHub Repository"
    ):

        repo_stats = repository_metrics(
            repo_path
        )

        code, file_count = collect_source_code(
            repo_path
        )

        repo_summary = generate_repository_summary(
            repo_stats,
            file_count
        )
        
        chart_data = get_repository_chart_data(
            repo_stats
        )

        repo_files = get_repository_files(
            repo_path
        )
        
        repository_findings = analyze_repository_static(
            repo_path,
            repo_files
        )
        
        repo_health_score = calculate_repository_health(
            repo_stats,
            repository_findings
        )

        file_risks = rank_repository_files(
            repo_path,
            repo_files
        )

        

        st.success(
            f"Repository contains {file_count} source files"
        )

        st.subheader(
            "Repository Summary"
        )

        st.info(
            repo_summary
        )

        repository_findings = analyze_repository_static(
            repo_path,
            repo_files
        )
        
        architecture_findings = analyze_repository_architecture(
            repo_path,
            repo_files
        )
        
        architecture_score = calculate_architecture_score(
            architecture_findings
        )

        repository_summary = generate_repository_executive_summary(
            repo_files,
            repository_findings,
            repo_health_score,
            file_risks
        )

        st.subheader(
            "Repository Executive Summary"
        )

        st.code(
            repository_summary
        )

        st.subheader(
            "Repository Health Score"
        )

        if repo_health_score >= 80:
            status = "Excellent"

        elif repo_health_score >= 60:
            status = "Good"

        elif repo_health_score >= 40:
            status = "Fair"

        else:
            status = "Poor"

        st.metric(
            "Health Score",
            f"{repo_health_score}/100"
        )

        st.write(
            f"Repository Status: {status}"
        )
        
        st.subheader(
            "Repository Overview"
        )

        df = pd.DataFrame(
            {
                "Metric": chart_data.keys(),
                "Value": chart_data.values()
            }
        )

        st.bar_chart(
            df.set_index("Metric")
        )
        
        st.subheader(
            "Repository Risk Ranking"
        )

        st.dataframe(
            file_risks,
            use_container_width=True
        )

        with st.sidebar:

            st.subheader(
                "Repository Files"
            )

            for file in repo_files:

                st.write(file)

        r1, r2, r3 = st.columns(3)

        with r1:

            st.metric(
                "Files",
                repo_stats["files"]
            )

            st.metric(
                "Lines",
                repo_stats["lines"]
            )

        with r2:

            st.metric(
                "Functions",
                repo_stats["functions"]
            )

            st.metric(
                "Classes",
                repo_stats["classes"]
            )

        with r3:

            st.metric(
                "Imports",
                repo_stats["imports"]
            )

            st.metric(
                "Avg Complexity",
                repo_stats["avg_complexity"]
            )

        st.divider()

    metrics = calculate_metrics(code)

    st.subheader(
        "Code Metrics"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Lines",
            metrics["lines"]
        )

        st.metric(
            "Functions",
            metrics["functions"]
        )

    with col2:

        st.metric(
            "Classes",
            metrics["classes"]
        )

        st.metric(
            "Imports",
            metrics["imports"]
        )

    with col3:

        st.metric(
            "Complexity",
            metrics["complexity_score"]
        )

        st.metric(
            "Risk",
            metrics["risk"]
        )

    st.divider()

    if analysis_mode == "Single File":

        st.subheader(
            "Uploaded Code"
        )

        st.code(
            code,
            language="python"
        )

    if st.button(
        "Analyze Code"
    ):

        with st.spinner(
            "Reviewing code..."
        ):

            if analysis_mode == "Single File":

                review = review_code(
                    code
                )
                
            elif analysis_mode == "Pull Request Review":

                pr_findings = review_pull_request(
                    pr_diff
            )

                review = format_static_findings(
                    pr_findings
            )

            else:

                review_results = review_repository(
                    repo_path,
                    repo_files
                )

                review = generate_repository_ai_summary(
                    review_results
                )
                
                repository_findings = analyze_repository_static(
                    repo_path,
                    repo_files
                )

                file_risks = rank_repository_files(
                    repo_path,
                    repo_files
                )

                repository_summary = generate_repository_executive_summary(
                    repo_files,
                    repository_findings,
                    repo_health_score,
                    file_risks
                )


            if analysis_mode == "Single File":

                static_findings = run_static_analysis(
                    code
                )
                
            elif analysis_mode == "Pull Request Review":

                static_findings = review_pull_request(
                    pr_diff
                )
                

            else:

                static_findings = analyze_repository_static(
                    repo_path,
                    repo_files
                )

            static_report = format_static_findings(
                static_findings
            )

            static_score = calculate_static_score(
                static_findings
            )
            
            security_score = calculate_security_score(
                static_findings
            )
            
            security_summary = summarize_security_findings(
                static_findings
            )

            

            severities = {
                "Critical": 0,
                "High": 0,
                "Medium": 0,
                "Low": 0
            }

            for finding in static_findings:

                severity = finding.get(
                    "severity",
                    ""
                )

                if severity in severities:

                    severities[severity] += 1
            
            severity_chart = get_severity_chart_data(
                severities
            )
            
            st.subheader(
                "Severity Distribution"
            )

            severity_df = pd.DataFrame(
                {
                    "Severity": severity_chart.keys(),
                    "Count": severity_chart.values()
                }
            )

            st.bar_chart(
                severity_df.set_index(
                    "Severity"
                )
            )

            score = extract_score(
                review
            )
            
            previous_score = get_previous_score()

            comparison = compare_versions(
                previous_score,
                score if score else 0
            )

            security_findings = [

                finding

                for finding in static_findings

                if any(
                    keyword in finding["type"]
                    for keyword in (
                        "Password",
                        "Token",
                        "Key",
                        "URL",
                        "Private"
                    )
                )
            ]

            security = format_static_findings(
                security_findings
            )

            performance_findings = [

                finding

                for finding in static_findings

                if finding["type"] in (
                    "Long Function",
                    "Deep Nesting"
                )
            ]

            performance = format_static_findings(
                performance_findings
            )

            smell_findings = [

                finding

                for finding in static_findings

                if finding["type"] in (
                    "Unused Variable",
                    "Unused Import",
                    "Duplicate Function",
                    "Too Many Parameters",
                    "Dead Function"
                )
            ]

            smells = format_static_findings(
                smell_findings
            )
            
            fix_suggestions = generate_fix_suggestions(
                static_findings
            )
            
            ai_fix_suggestions = generate_ai_fix_suggestions(
                code,
                static_findings
            )
            
            
            executive_summary = generate_executive_summary(
                score if score else 0,
                static_score,
                security_score,
                static_findings,
                severities
            )

            pdf_file = generate_pdf(
                "review_report.pdf",
                score if score else 0,
                executive_summary,
                security,
                performance,
                smells,
                review
            )

        st.divider()

        if score is not None:

            st.subheader(
                "Code Quality Score"
            )

            st.metric(
                "Score",
                f"{score}/100"
            )

        st.subheader(
            "Severity Dashboard"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.metric(
                "Critical",
                severities["Critical"]
            )

        with c2:

            st.metric(
                "High",
                severities["High"]
            )

        with c3:

            st.metric(
                "Medium",
                severities["Medium"]
            )

        with c4:

            st.metric(
                "Low",
                severities["Low"]
            )

        st.divider()

        tab1, tab2, tab3, tab4, tab5 ,tab6 ,tab7 ,tab8, tab9 = st.tabs(
            [
                "Summary",
                "Security",
                "Performance",
                "Code Smells",
                "Fix Suggestions",
                "Full Report",
                "Static Analysis",
                "Architecture",
                "History"
            ]
        )

        with tab1:

            if score is not None:

                st.metric(
                    "Code Quality Score",
                    f"{score}/100"
                )
                
                st.metric(
                    "Static Analysis Score",
                    f"{static_score}/100"
                )
                
                st.metric(
                    "Security Score",
                    f"{security_score}/100"
                )

            st.write(
                f"Critical Issues: {severities['Critical']}"
            )

            st.write(
                f"High Issues: {severities['High']}"
            )

            st.write(
                f"Medium Issues: {severities['Medium']}"
            )

            st.write(
                f"Low Issues: {severities['Low']}"
            )

        with tab2:

            st.subheader(
                "Security Dashboard"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:

                st.metric(
                    "Critical",
                    security_summary["critical"]
                )

            with c2:

                st.metric(
                    "High",
                    security_summary["high"]
                )

            with c3:

                st.metric(
                    "Medium",
                    security_summary["medium"]
                )

            with c4:

                st.metric(
                    "Low",
                    security_summary["low"]
                )

            st.divider()

            st.subheader(
                "Detected Security Issues"
            )

            for issue in security_summary["types"]:

                st.write(
                    f"• {issue}"
                )

            st.divider()

            st.error(
                security
            )
        with tab3:

            st.warning(
                performance
            )

        with tab4:

            st.info(
                smells
            )
            
        with tab5:

            st.subheader(
                "AI Fix Suggestions"
            )

            st.markdown(
                ai_fix_suggestions
            )

        with tab6:

            st.markdown(
                review
            )
            
        with tab7:

            st.markdown(
                f"```text\n{static_report}\n```"
            )
            
        with tab8:

            st.subheader(
                "Repository Architecture Analysis"
            )

            st.metric(
                "Architecture Score",
                f"{architecture_score}/100"
            )

            st.divider()

            if architecture_findings:

                for finding in architecture_findings:

                    st.warning(
                        f"{finding['type']} - "
                        f"{finding['message']}"
                    )

            else:

                st.success(
                    "No architecture issues detected."
                )
                
                
            with tab9:

                st.subheader(
                    "Historical Comparison"
                )

                st.metric(
                    "Previous Score",
                    comparison["old_score"]
                )

                st.metric(
                    "Current Score",
                    comparison["new_score"]
                )

                st.metric(
                    "Difference",
                    comparison["difference"]
                )

                st.info(
                    f"Status: {comparison['status']}"
                )

        with open(
            pdf_file,
            "rb"
        ) as pdf:

            st.download_button(
                label="Download PDF Report",
                data=pdf,
                file_name="IntelliReview_Report.pdf",
                mime="application/pdf"
            )

        st.download_button(
            label="Download TXT Report",
            data=review,
            file_name="review_report.txt",
            mime="text/plain"
        )
