# CEBAFEX Agri visual system

Product: an agricultural operations workspace built with Streamlit. The supplied company logo is preserved without recolouring, distortion or text edits. The user-specified company name is CEBAFEX. Tamil mode uses a localized company wordmark so embedded Latin logo text does not break the selected-language requirement.

The UI/UX design search returned the Data-Dense Dashboard style for internal analytics, a suitable match for stock tables, crop filters, financial figures and operational reports. Its marketing-page suggestions were not adopted for the working application. The navy/cyan palette is adapted to the supplied logo. No testimonials, live counters, customer logos or business claims are invented.

- Primary: #075C86, on-primary white.
- Brand/navy: #0B2540.
- Cyan illustration/accent: #00A0C6; use darker blue for normal text.
- Teal data accent: #087F8C.
- Main text: #152D43; secondary text: #52677A.
- Background: #F3F6FA; card: white; border: #DCE5ED.
- Pending state: pale amber with #82570A text; state also has a written label.
- Typography: local system sans serif for English; bundled Noto Sans Tamil for Tamil. No external font request.
- Space scale: 4, 8, 12, 16, 20, 24, 32, 40, 48 px.
- Card radius: 12px; controls: 8px; visible focus: 3px teal.
- Sidebar provides predictable destinations; action buttons route through canonical navigation state.
- Actual calculated values only. Full text explanations accompany charts. Unknown buyer data remains unknown.
- Preserve keyboard use, reduced-motion support, labelled fields, scrollable tables, responsive gutters and 44px primary controls.

Style lives in static/brand/business.css. Reusable brand components live in harvest/brand.py. Business logic must remain separate from presentation.
