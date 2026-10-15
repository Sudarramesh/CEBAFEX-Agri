# CEBAFEX calculation acceptance walkthrough

Run the app from the README instructions. Start a fresh browser session with no saved workspace restored. Use English for this script; repeat in Tamil with the translated controls to verify the same numbers. Application text follows the selected language throughout.

| Time | Screen and action | Acceptance evidence |
|---|---|---|
| 0:00–0:20 | Home: select language, review introduction and click Get Started | Opens Upload Data; sidebar navigation works |
| 0:20–1:20 | Upload Data: agriculture → upload agriculture_messy_demo.csv → inspect suggestions → Validate and activate | Record 3 has a missing market price; activation rejected, no silent correction |
| 1:20–1:50 | Upload agriculture_demo.csv → inspect/edit mappings → Validate and activate; choose Buyers and upload buyers_demo.csv → validate | Both original CSVs become the shared validated workspace; buyers remain sample opportunities |
| 1:50–2:25 | Dashboard: use all crops | 3 records; 1,050 kg available; 850 kg uploaded estimated demand; 250 kg positive surplus; 50 kg shortages |
| 2:25–3:00 | Surplus and Risk: review rules and priority | Tomatoes: 500 − 300 = 200 kg surplus; Onions 50 kg surplus; Carrots 50 kg shortage; ranking and adjustable planning rules explained |
| 3:00–3:35 | Buyer Matching: select Tomatoes | 200 kg potential surplus; 180 kg potentially matched; 20 kg unmatched. Source order and allocation caps shown; repeat without accumulating allocations |
| 3:35–4:15 | Profit Analysis: select Tomatoes | Green Leaf: 100 × ₹28 − ₹200 = ₹2,600. City Hostel: 80 × ₹26 − ₹250 = ₹1,830. Combined after transport: ₹4,430. Buyer gross ₹4,880 minus transport ₹450 |
| 4:15–4:45 | AI Assistant: use suggested priority question | Recommends Tomatoes using current 200 kg surplus, 180 kg preview, 20 kg remaining and ₹4,430 return; shows evidence and calculation sources |
| 4:45–5:00 | Switch language, revisit assistant, expand Data and reports and save snapshot | Existing answer rerenders in selected language; canonical dataset and calculations stay unchanged; saved workspace can be restored |

The missing-price sample is deliberately invalid. Its corrected counterpart is the exact original agriculture_demo.csv, not an imputed record. File paths are relative to `data/` in the project.

Uploaded demand is an estimate, not a model forecast. Risk thresholds are planning choices, not a crop shelf-life prediction. Matches are sample opportunities, never confirmed orders. Returns subtract quoted buyer transport but are not profit: production and other costs are unknown. For the same 180 kg, the market gross reference is ₹4,500 before unknown market costs, so the displayed buyer-return minus market-gross difference is −₹70; this is not a profit comparison.

The original request mentions an attached judging demo, but no separate attachment was available in the supplied workspace. This walkthrough implements the explicit seven-screen and numeric acceptance contract in the request.
