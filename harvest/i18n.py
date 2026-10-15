"""Strict English/Tamil catalogs; canonical uploaded data is kept separately."""
LABELS = {
 "Home": "முகப்பு", "Upload Data": "தரவைப் பதிவேற்று", "Dashboard": "தரவுப் பலகை",
 "Surplus and Risk": "உபரி மற்றும் அபாயம்", "Buyer Matching": "வாங்குபவர் பொருத்தம்",
 "Profit Analysis": "லாபப் பகுப்பாய்வு", "AI Assistant": "செயற்கை நுண்ணறிவு உதவியாளர்",
 "Load demo data": "மாதிரித் தரவை ஏற்று", "Validate and activate": "சரிபார்த்து பயன்படுத்து",
 "Uploaded records": "பதிவேற்றிய பதிவுகள்", "Available (kg)": "கிடைக்கும் அளவு (கிலோ)",
 "Estimated demand (kg)": "மதிப்பிடப்பட்ட தேவை (கிலோ)",
 "Potential surplus (kg)": "சாத்தியமான உபரி (கிலோ)", "Shortage (kg)": "பற்றாக்குறை (கிலோ)",
 "Navigation": "வழிசெலுத்தல்", "Save local snapshot": "உள்ளூரில் தரவைச் சேமி",
 "Restore local snapshot": "சேமித்த தரவை மீட்டெடு",
 "Upload agriculture CSV": "வேளாண் CSV கோப்பைப் பதிவேற்று",
 "Column mapping": "நெடுவரிசைப் பொருத்தம்", "Quality summary": "தரவுத் தரச் சுருக்கம்",
 "Active validated data": "சரிபார்க்கப்பட்ட நடப்புத் தரவு",
 "Download agriculture sample": "வேளாண் மாதிரியைப் பதிவிறக்கு",
 "Download buyers sample": "வாங்குபவர் மாதிரியைப் பதிவிறக்கு",
}


LABELS.update({
 "Agriculture": "வேளாண்மை", "Buyers": "வாங்குபவர்கள்", "Upload buyers CSV": "வாங்குபவர் CSV பதிவேற்று",
 "Crop filter": "பயிர் வடிகட்டி", "Data provenance": "தரவு மூலம் மற்றும் விவரங்கள்",
 "Download filtered balances": "வடிகட்டிய கணக்குகளைப் பதிவிறக்கு",
 "Download validated CSV": "சரிபார்த்த CSV பதிவிறக்கு", "Download issue report": "பிழை அறிக்கை பதிவிறக்கு",
 "Row issues": "பதிவுப் பிழைகள்", "Input records": "உள்ளீட்டுப் பதிவுகள்",
 "Valid records": "சரியான பதிவுகள்", "Invalid records": "தவறான பதிவுகள்",
 "Duplicate records": "நகல் பதிவுகள்", "Missing cells": "விடுபட்ட மதிப்புகள்",
 "Active buyers": "நடப்பு வாங்குபவர்கள்", "Preview": "முன்னோட்டம்",
 "crop": "பயிர்", "available_kg": "கிடைக்கும் அளவு (கிலோ)",
 "estimated_demand_kg": "மதிப்பிடப்பட்ட தேவை (கிலோ)", "market_price_per_kg": "சந்தை விலை (₹/கிலோ)",
 "harvest_age_days": "அறுவடைக்குப் பின் நாட்கள்", "buyer_name": "வாங்குபவர் பெயர்",
 "buyer_type": "வாங்குபவர் வகை", "required_kg": "தேவையான அளவு (கிலோ)",
 "offer_price_per_kg": "வழங்கும் விலை (₹/கிலோ)", "transport_cost": "போக்குவரத்துச் செலவு (₹)",
 "potential_surplus_kg": "சாத்தியமான உபரி (கிலோ)", "shortage_kg": "பற்றாக்குறை (கிலோ)",
 "No crops selected": "பயிர்கள் தேர்ந்தெடுக்கப்படவில்லை",
 "Dataset type": "தரவு வகை", "Crop": "பயிர்", "Quantity (kg)": "அளவு (கிலோ)",
 "Measure": "அளவீடு", "No active dataset": "நடப்புத் தரவு இல்லை",
 "Phase 2: upload, validate and explore": "கட்டம் 2: பதிவேற்றி சரிபார்த்து ஆராயவும்",
 "No model-generated forecast": "மாதிரி உருவாக்கிய முன்னறிவிப்பு இல்லை",
 "Sample opportunities only; not confirmed orders": "மாதிரி வாய்ப்புகள் மட்டுமே; உறுதியான ஆர்டர்கள் அல்ல",
 "Uploaded opportunities; not confirmed orders": "பதிவேற்றிய வாய்ப்புகள்; உறுதியான ஆர்டர்கள் அல்ல",
 "Validated and active": "சரிபார்க்கப்பட்டு பயன்பாட்டில் உள்ளது",
 "Fix errors and validate again; previous active data is preserved": "பிழைகளைத் திருத்தி மீண்டும் சரிபார்க்கவும்; நடப்புத் தரவு பாதுகாக்கப்பட்டுள்ளது",
 "Match compatibility": "தரவுப் பொருந்துதன்மை",
})

LABELS['Unassessed records'] = 'மதிப்பிடப்படாத பதிவுகள்'

LABELS.update({
 "Phase 3: understand surplus and review risks": "கட்டம் 3: உபரி மற்றும் அபாயப் பரிசீலனை",
 "Planning signals only; not measured spoilage or shelf life": "திட்டமிடும் அறிகுறிகள் மட்டுமே; அழுகல் அல்லது ஆயுள் அளவீடு அல்ல",
 "Planning assumptions": "திட்டமிடும் அனுமானங்கள்", "Large surplus threshold (%)": "அதிக உபரி வரம்பு (%)",
 "Harvest age review threshold (days)": "அறுவடை வயது பரிசீலனை வரம்பு (நாட்கள்)",
 "Apply planning rules": "திட்டமிடும் விதிகளைப் பயன்படுத்து", "Planning rules applied": "விதிகள் பயன்படுத்தப்பட்டன",
 "First crop to review for surplus selling": "உபரி விற்பனைக்காக முதலில் பரிசீலிக்க வேண்டிய பயிர்",
 "Priority uses the full active dataset; filters below only change the report view": "முன்னுரிமை முழு நடப்புத் தரவிற்கானது; கீழுள்ள வடிகட்டி அறிக்கையை மட்டும் மாற்றும்",
 "No positive surplus; no crop prioritised for surplus selling": "உபரி இல்லை; உபரி விற்பனை முன்னுரிமை இல்லை",
 "Selling priority: largest positive surplus, then older harvest, then crop name": "விற்பனை முன்னுரிமை: அதிக உபரி, அடுத்து அறுவடை வயது, அடுத்து பயிர்ப் பெயர்",
 "Surplus and shortage overview": "உபரி மற்றும் பற்றாக்குறைச் சுருக்கம்", "High review crops": "அதிக பரிசீலனை தேவைப்படும் பயிர்கள்",
 "Overview totals use all active crops": "சுருக்கக் கணக்குகள் அனைத்து நடப்புப் பயிர்களுக்கும்",
 "Review category filter": "பரிசீலனைப் பிரிவு வடிகட்டி", "No records match this filter": "இந்த வடிகட்டிக்கு பதிவுகள் இல்லை",
 "High": "அதிகம்", "Moderate": "மிதம்", "Low": "குறைவு", "No surplus": "உபரி இல்லை",
 "Potential surplus": "சாத்தியமான உபரி", "Shortage": "பற்றாக்குறை", "Balanced": "சமநிலை",
 "Yes": "ஆம்", "No": "இல்லை", "surplus_ratio": "உபரி விகிதம்", "balance_status": "இருப்பு நிலை",
 "high_surplus_flag": "அதிக உபரி அறிகுறி", "age_review_flag": "அறுவடை வயது பரிசீலனை",
 "review_score": "பரிசீலனை மதிப்பெண் (0–2)", "review_level": "பரிசீலனை நிலை",
 "priority_rank": "விற்பனை முன்னுரிமை", "reason": "கணக்கீட்டு விளக்கம்",
 "Review shortage separately; this crop has no surplus to allocate": "பற்றாக்குறையைத் தனியாகப் பரிசீலிக்கவும்; ஒதுக்க உபரி இல்லை",
 "Inspect stock condition; age alone does not prove spoilage": "இருப்பின் நிலையைச் சோதிக்கவும்; வயது மட்டும் அழுகலை நிரூபிக்காது",
 "Download risk report": "உபரி பரிசீலனை அறிக்கையைப் பதிவிறக்கு", "Download planning policy": "திட்டமிடும் விதிகளைப் பதிவிறக்கு",
})

LABELS.update({
 "Phase 4: explore potential buyer matches": "கட்டம் 4: சாத்தியமான வாங்குபவர் பொருத்தங்கள்",
 "Load agriculture data before buyer matching": "வாங்குபவர் பொருத்தத்திற்கு முன் வேளாண் தரவை ஏற்றவும்",
 "Load buyer opportunities in Upload Data or use Load demo data": "வாங்குபவர் தரவைப் பதிவேற்றவும் அல்லது மாதிரித் தரவை ஏற்றவும்",
 "Preview only: no stock reserved, no buyer contacted, no order created": "முன்னோட்டம் மட்டுமே: இருப்பு முன்பதிவு, வாங்குபவர் தொடர்பு அல்லது ஆர்டர் இல்லை",
 "Allocation rules": "ஒதுக்கீட்டு விதிகள்",
 "Buyer rows are processed once in CSV source order; earlier rows get surplus first": "CSV வரிசைப்படி ஒவ்வொரு பதிவும் ஒருமுறை; முந்தைய பதிவுகளுக்கு முதலில் உபரி",
 "Each allocation is capped at the buyer request and remaining positive crop surplus": "ஒதுக்கீடு வாங்குபவர் தேவை மற்றும் மீதமுள்ள உபரிக்கு உட்பட்டது",
 "This is a deterministic preview, not an optimal-profit allocation": "இது நிர்ணயிக்கப்பட்ட முன்னோட்டம்; அதிக லாப ஒதுக்கீடு அல்ல",
 "Matching crop filter": "பொருத்தப் பயிர் வடிகட்டி", "All crops": "அனைத்துப் பயிர்கள்",
 "Filters change the view only; allocation source order and full-dataset calculations stay unchanged": "வடிகட்டி காட்சியை மட்டும் மாற்றும்; ஒதுக்கீட்டு வரிசை மற்றும் முழுத் தரவுக் கணக்குகள் தொடரும்",
 "Potentially matched (kg)": "சாத்தியமாகப் பொருந்திய அளவு (கிலோ)", "Still unmatched (kg)": "இன்னும் பொருந்தாத அளவு (கிலோ)",
 "Matching totals reflect the selected crop; All crops shows full-dataset totals": "கணக்குகள் தேர்ந்தெடுத்த பயிருக்கானவை; அனைத்துப் பயிர்கள் முழுக் கணக்கைக் காட்டும்",
 "Crop allocation summary": "பயிர் ஒதுக்கீட்டுச் சுருக்கம்", "Potential buyer allocations": "சாத்தியமான வாங்குபவர் ஒதுக்கீடுகள்",
 "Selected crop has no agriculture record and no allocatable surplus": "தேர்ந்த பயிருக்கு வேளாண் பதிவு அல்லது ஒதுக்கக்கூடிய உபரி இல்லை",
 "No potential allocations for this view; see the audit for reasons": "இந்தக் காட்சியில் ஒதுக்கீடு இல்லை; விளக்கத்தைப் பார்க்கவும்",
 "Returns after transport are estimates, not profit; production and other costs are unknown": "போக்குவரத்துக்குப் பிந்தைய வருவாய் மதிப்பீடு; லாபம் அல்ல; பிற செலவுகள் தெரியவில்லை",
 "Some allocated opportunities have negative returns after transport; review before acting": "சில வாய்ப்புகளில் போக்குவரத்துக்குப் பின் எதிர்மறை வருவாய்; பரிசீலிக்கவும்",
 "Buyer allocation audit": "வாங்குபவர் ஒதுக்கீட்டு விளக்கம்",
 "Audit includes unmatched requests and source record numbers, in allocation order": "ஒதுக்கீட்டு வரிசையில் பொருந்தாத தேவைகளும் மூலப் பதிவு எண்களும் காட்டப்படும்",
 "Unfilled buyer requests are separate from crop shortages and unmatched crop surplus": "நிறைவேறாத வாங்குபவர் தேவை, பயிர்ப் பற்றாக்குறை மற்றும் மீதமுள்ள உபரி தனித்தனியானவை",
 "Download allocation audit": "ஒதுக்கீட்டு விளக்கத்தைப் பதிவிறக்கு", "Download crop matching summary": "பயிர் பொருத்தச் சுருக்கத்தைப் பதிவிறக்கு",
 "Download matching provenance": "பொருத்தத் தரவு விவரங்களைப் பதிவிறக்கு", "Agriculture source": "வேளாண் தரவு மூலம்", "Buyer source": "வாங்குபவர் தரவு மூலம்",
 "Potential full match": "சாத்தியமான முழுப் பொருத்தம்", "Potential partial match": "சாத்தியமான பகுதி பொருத்தம்",
 "Crop unavailable": "பயிர் கிடைக்கவில்லை", "Zero request": "தேவை பூஜ்ஜியம்", "Surplus exhausted": "உபரி தீர்ந்தது",
 "matched_kg": "சாத்தியமாகப் பொருந்திய அளவு (கிலோ)", "unmatched_kg": "மீதமுள்ள உபரி (கிலோ)",
 "estimated_return_after_transport": "போக்குவரத்துக்குப் பிந்தைய மதிப்பிடப்பட்ட வருவாய் (₹)",
 "source_record": "மூலப் பதிவு எண்", "surplus_before_kg": "முன் உபரி (கிலோ)", "surplus_after_kg": "பின் உபரி (கிலோ)",
 "unfilled_request_kg": "நிறைவேறாத வாங்குபவர் தேவை (கிலோ)", "status": "நிலை", "charged_transport_cost": "கணக்கிட்ட போக்குவரத்துச் செலவு (₹)",
})

LABELS.update({
 "Phase 5: compare estimated returns": "கட்டம் 5: மதிப்பிடப்பட்ட வருவாய் ஒப்பீடு",
 "Load agriculture data before financial analysis": "நிதிப் பகுப்பாய்வுக்கு முன் வேளாண் தரவை ஏற்றவும்",
 "Estimated returns after transport, not profit; production and other costs are unknown": "போக்குவரத்துக்குப் பிந்தைய மதிப்பிடப்பட்ட வருவாய்; லாபம் அல்ல; பிற செலவுகள் தெரியவில்லை",
 "The page is named Profit Analysis for navigation; profit cannot be calculated from the supplied fields": "திரைப் பெயர் லாபப் பகுப்பாய்வு; வழங்கிய தரவால் உண்மையான லாபத்தைக் கணக்கிட முடியாது",
 "Financial crop filter": "நிதிப் பயிர் வடிகட்டி",
 "Financial totals use the selected matched quantities; allocation order is unchanged": "நிதிக் கணக்குகள் தேர்ந்த பயிரின் பொருந்திய அளவிற்கானவை; ஒதுக்கீட்டு வரிசை மாறாது",
 "Buyer gross revenue (₹)": "வாங்குபவர் மொத்த வருவாய் (₹)", "Buyer transport charged (₹)": "வாங்குபவர் போக்குவரத்துச் செலவு (₹)",
 "Buyer return after transport (₹)": "போக்குவரத்துக்குப் பின் வாங்குபவர் வருவாய் (₹)",
 "No matched quantity in this view; no buyer revenue or transport is assumed": "பொருந்திய அளவு இல்லை; வருவாய் அல்லது போக்குவரத்து கணக்கிடப்படவில்லை",
 "Buyer calculation breakdown": "வாங்குபவர் கணக்கீட்டு விவரம்",
 "Buyer gross = matched kg × offer price; return after transport subtracts the full quoted trip cost once": "மொத்த வருவாய் = பொருந்திய கிலோ × விலை; போக்குவரத்துச் செலவு ஒருமுறை கழிக்கப்படும்",
 "Market gross reference (₹)": "சந்தை மொத்தக் குறிப்பு மதிப்பு (₹)", "Difference versus gross reference (₹)": "மொத்தக் குறிப்பு மதிப்புடன் வேறுபாடு (₹)",
 "Calculation": "கணக்கீடு", "Partial allocations incur the full buyer transport quote; zero allocation incurs no trip": "பகுதி ஒதுக்கீட்டுக்கும் முழுப் போக்குவரத்துச் செலவு; ஒதுக்கீடு இல்லையெனில் பயணம் இல்லை",
 "Compare the same matched quantities": "அதே பொருந்திய அளவுகளை ஒப்பிடவும்",
 "Market reference = matched kg × uploaded market price, before market transport and other costs": "சந்தைக் குறிப்பு = பொருந்திய கிலோ × பதிவேற்றிய சந்தை விலை; செலவுகளுக்கு முன்",
 "Market transport is unknown by default; the gross reference is not a net return or a confirmed sale": "சந்தைப் போக்குவரத்துச் செலவு தெரியவில்லை; இது நிகர வருவாய் அல்லது உறுதியான விற்பனை அல்ல",
 "Difference = buyer return after transport minus market gross reference; it is not a net advantage or profit": "வேறுபாடு = போக்குவரத்துக்குப் பின் வாங்குபவர் வருவாய் − சந்தை மொத்தக் குறிப்பு; இது நிகர ஆதாயம் அல்லது லாபம் அல்ல",
 "Reference type": "ஒப்பீட்டு வகை", "Optional market transport scenario": "விருப்ப சந்தைப் போக்குவரத்து அனுமானம்",
 "Enter one total market transport assumption for only the selected matched quantity": "தேர்ந்த பொருந்திய அளவிற்கான மொத்தச் சந்தைப் போக்குவரத்துச் செலவை உள்ளிடவும்",
 "I want to supply a market transport assumption": "சந்தைப் போக்குவரத்துச் செலவு அனுமானத்தை வழங்குகிறேன்",
 "Assumed total market transport (₹)": "அனுமான மொத்தச் சந்தைப் போக்குவரத்து (₹)",
 "Market return after assumed transport (₹)": "அனுமானப் போக்குவரத்துக்குப் பின் சந்தை வருவாய் (₹)",
 "Buyer difference versus market scenario (₹)": "சந்தை அனுமானத்துடன் வாங்குபவர் வருவாய் வேறுபாடு (₹)",
 "User assumption only; an entered zero explicitly assumes zero transport. Other costs remain unknown": "பயனர் அனுமானம் மட்டும்; பூஜ்ஜியம் செலவு இல்லை எனக் கருதும்; பிற செலவுகள் தெரியவில்லை",
 "This scenario is session-only and is not included in workspace snapshots": "இந்த அனுமானம் நடப்பு அமர்விற்கு மட்டும்; சேமித்த தரவில் சேராது",
 "Unmatched surplus stays separate": "பொருந்தாத உபரி தனியாக உள்ளது",
 "Unmatched market reference before costs; not booked or matched revenue": "பொருந்தாத உபரியின் செலவுக்கு முந்தைய குறிப்பு; ஈட்டிய வருவாய் அல்ல",
 "Never add unmatched reference value to buyer revenue; no buyer allocation exists for it": "பொருந்தாத உபரியை வாங்குபவர் வருவாயுடன் சேர்க்கக்கூடாது; அதற்கு ஒதுக்கீடு இல்லை",
 "Download buyer financial report": "வாங்குபவர் நிதி அறிக்கை பதிவிறக்கு", "Download crop financial summary": "பயிர் நிதிச் சுருக்கம் பதிவிறக்கு",
 "Download financial assumptions and totals": "நிதி அனுமானங்கள் மற்றும் கணக்குகள் பதிவிறக்கு",
 "unmatched_market_reference": "பொருந்தாத உபரியின் குறிப்பு மதிப்பு (₹)",
})

# Static sentences inherited from the previous phases.
PAIRED = {'Agricultural records → practical selling decisions / வேளாண் தரவிலிருந்து விற்பனை முடிவுகள்': ('Agricultural records → practical selling decisions', 'வேளாண் தரவிலிருந்து விற்பனை முடிவுகள்'), 'Understand crop availability and estimated demand before planning a sale. / விற்பனைக்கு முன் பயிர் இருப்பையும் மதிப்பிடப்பட்ட தேவையையும் அறியவும்.': ('Understand crop availability and estimated demand before planning a sale.', 'விற்பனைக்கு முன் பயிர் இருப்பையும் மதிப்பிடப்பட்ட தேவையையும் அறியவும்.'), 'Load demo data → Dashboard, or Upload Data → map columns → validate → explore. / மாதிரித் தரவு → தரவுப் பலகை; அல்லது பதிவேற்று → பொருத்து → சரிபார்.': ('Load demo data → Dashboard, or Upload Data → map columns → validate → explore.', 'மாதிரித் தரவு → தரவுப் பலகை; அல்லது பதிவேற்று → பொருத்து → சரிபார்.'), 'Phase 2 adds agriculture and buyer uploads, record-level quality reports, source metadata, crop filters and local workspace snapshots. / வேளாண் மற்றும் வாங்குபவர் பதிவேற்றம், தர அறிக்கை, வடிகட்டிகள் மற்றும் உள்ளூர் சேமிப்பு.': ('Phase 2 adds agriculture and buyer uploads, record-level quality reports, source metadata, crop filters and local workspace snapshots.', 'வேளாண் மற்றும் வாங்குபவர் பதிவேற்றம், தர அறிக்கை, வடிகட்டிகள் மற்றும் உள்ளூர் சேமிப்பு.'), 'Phase 3 adds transparent surplus review flags, editable planning thresholds and a calculated crop priority. / கட்டம் 3: உபரி பரிசீலனை, மாற்றக்கூடிய வரம்புகள் மற்றும் பயிர் முன்னுரிமை.': ('Phase 3 adds transparent surplus review flags, editable planning thresholds and a calculated crop priority.', 'கட்டம் 3: உபரி பரிசீலனை, மாற்றக்கூடிய வரம்புகள் மற்றும் பயிர் முன்னுரிமை.'), 'Phase 4 adds capped buyer previews, unmatched quantities and a source-order audit. / கட்டம் 4: வரம்புடைய வாங்குபவர் பொருத்தம் மற்றும் ஒதுக்கீட்டு விளக்கம்.': ('Phase 4 adds capped buyer previews, unmatched quantities and a source-order audit.', 'கட்டம் 4: வரம்புடைய வாங்குபவர் பொருத்தம் மற்றும் ஒதுக்கீட்டு விளக்கம்.'), 'Phase 5 compares matched buyer returns with a market-price reference and explicit transport assumptions. / கட்டம் 5: வாங்குபவர் வருவாய் மற்றும் சந்தை விலை ஒப்பீடு.': ('Phase 5 compares matched buyer returns with a market-price reference and explicit transport assumptions.', 'கட்டம் 5: வாங்குபவர் வருவாய் மற்றும் சந்தை விலை ஒப்பீடு.'), 'Demand remains an uploaded estimate. No live market feed or model forecast is generated. / தேவை பதிவேற்றிய மதிப்பீடு; நேரடிச் சந்தைத் தரவு அல்லது மாதிரி முன்னறிவிப்பு இல்லை.': ('Demand remains an uploaded estimate. No live market feed or model forecast is generated.', 'தேவை பதிவேற்றிய மதிப்பீடு; நேரடிச் சந்தைத் தரவு அல்லது மாதிரி முன்னறிவிப்பு இல்லை.'), 'Planned screen / திட்டமிடப்பட்ட திரை. Detailed workflows will be added in later requested phases.': ('Planned screen', 'திட்டமிடப்பட்ட திரை. Detailed workflows will be added in later requested phases.'), 'All screens share the active validated agriculture and buyer datasets. / எல்லாத் திரைகளும் சரிபார்க்கப்பட்ட நடப்புத் தரவுகளைப் பகிர்கின்றன.': ('All screens share the active validated agriculture and buyer datasets.', 'எல்லாத் திரைகளும் சரிபார்க்கப்பட்ட நடப்புத் தரவுகளைப் பகிர்கின்றன.'), 'Currency: gross lines and charged trip costs are rounded to paise (decimal half-up), then subtracted; totals sum those lines. / பண மதிப்புகள் பைசாவிற்கு முழுமையாக்கப்படும்.': ('Currency: gross lines and charged trip costs are rounded to paise (decimal half-up), then subtracted; totals sum those lines.', 'பண மதிப்புகள் பைசாவிற்கு முழுமையாக்கப்படும்.'), 'kg · ₹/kg · days / நாட்கள். Transport is ₹ per buyer trip / போக்குவரத்து ₹ ஒரு பயணத்திற்கு.': ('kg · ₹/kg · days', 'நாட்கள். Transport is ₹ per buyer trip / போக்குவரத்து ₹ ஒரு பயணத்திற்கு.'), 'KPIs and charts below reflect selected crops only / கீழுள்ள கணக்குகள் தேர்ந்தெடுத்த பயிர்களுக்கு மட்டும்.': ('KPIs and charts below reflect selected crops only', 'கீழுள்ள கணக்குகள் தேர்ந்தெடுத்த பயிர்களுக்கு மட்டும்.'), 'Surplus = max(available − uploaded estimated demand, 0). Shortage = max(demand − available, 0). Summed separately / உபரி மற்றும் பற்றாக்குறை தனித்தனியாகக் கணக்கிடப்படுகின்றன.': ('Surplus = max(available − uploaded estimated demand, 0). Shortage = max(demand − available, 0). Summed separately', 'உபரி மற்றும் பற்றாக்குறை தனித்தனியாகக் கணக்கிடப்படுகின்றன.'), 'Record numbers start at 1 after the header / தலைப்புக்குப் பின் பதிவு எண் 1 இல் தொடங்கும்.': ('Record numbers start at 1 after the header', 'தலைப்புக்குப் பின் பதிவு எண் 1 இல் தொடங்கும்.'), 'Load demo data or validate an agriculture CSV first / முதலில் வேளாண் தரவை ஏற்றவும்': ('Load demo data or validate an agriculture CSV first', 'முதலில் வேளாண் தரவை ஏற்றவும்'), 'Choose each source column once. Ambiguous suggestions are left blank / குழப்பமான பொருத்தங்களைத் தேர்ந்தெடுக்கவும்.': ('Choose each source column once. Ambiguous suggestions are left blank', 'குழப்பமான பொருத்தங்களைத் தேர்ந்தெடுக்கவும்.'), 'Coverage checks crop names only; allocations are not calculated here / பயிர்ப் பெயர்கள் மட்டும் ஒப்பிடப்படுகின்றன.': ('Coverage checks crop names only; allocations are not calculated here', 'பயிர்ப் பெயர்கள் மட்டும் ஒப்பிடப்படுகின்றன.'), 'Demo defaults are adjustable planning choices, not crop-specific science. / மாதிரி வரம்புகள் திட்டமிடும் தேர்வுகள்; பயிரின் ஆயுள் குறித்த அறிவியல் முடிவுகள் அல்ல.': ('Demo defaults are adjustable planning choices, not crop-specific science.', 'மாதிரி வரம்புகள் திட்டமிடும் தேர்வுகள்; பயிரின் ஆயுள் குறித்த அறிவியல் முடிவுகள் அல்ல.'), 'These are review categories, not probabilities. No temperature, storage condition or crop shelf-life data is available. / இவை பரிசீலனைப் பிரிவுகள்; அழுகும் நிகழ்தகவு அல்ல.': ('These are review categories, not probabilities. No temperature, storage condition or crop shelf-life data is available.', 'இவை பரிசீலனைப் பிரிவுகள்; அழுகும் நிகழ்தகவு அல்ல.'), 'Crop names match ignoring case/outer whitespace. Duplicate buyer/crop identities are rejected on upload. / பயிர்ப் பெயர்கள் பொருத்தப்படுகின்றன; நகல் வாங்குபவர்/பயிர் பதிவுகள் நிராகரிக்கப்படும்.': ('Crop names match ignoring case/outer whitespace. Duplicate buyer/crop identities are rejected on upload.', 'பயிர்ப் பெயர்கள் பொருத்தப்படுகின்றன; நகல் வாங்குபவர்/பயிர் பதிவுகள் நிராகரிக்கப்படும்.'), 'Estimated return after transport = matched kg × offer ₹/kg − full quoted transport. No allocation means no trip/cost. / போக்குவரத்துக்குப் பிந்தைய வருவாய் = ஒதுக்கிய கிலோ × விலை − போக்குவரத்து.': ('Estimated return after transport = matched kg × offer ₹/kg − full quoted transport. No allocation means no trip/cost.', 'போக்குவரத்துக்குப் பிந்தைய வருவாய் = ஒதுக்கிய கிலோ × விலை − போக்குவரத்து.')}

# One selected language per rendered sentence; never concatenate translations.
EXTRA = {
 'Language': 'மொழி', 'English': 'ஆங்கிலம்', 'Tamil': 'தமிழ்', 'தமிழ்': 'தமிழ்',
 'Harvest Intelligence AI': 'அறுவடை நுண்ணறிவு', 'HARVEST': 'அறுவடை',
 'Phase 6: ask the data-grounded assistant': 'கட்டம் 6: தரவை அடிப்படையாகக் கொண்ட உதவியாளரிடம் கேளுங்கள்',
 'Selected file': 'தேர்ந்தெடுத்த கோப்பு', 'Select column': 'நெடுவரிசையைத் தேர்ந்தெடுக்கவும்',
 'Source column {n}': 'மூல நெடுவரிசை {n}', 'Source file {n}': 'மூலக் கோப்பு {n}',
 'Crop {n}': 'பயிர் {n}', 'Buyer {n}': 'வாங்குபவர் {n}', 'Text {n}': 'உரை {n}',
 'Saved': 'சேமிக்கப்பட்டது', 'Restored': 'மீட்டெடுக்கப்பட்டது', 'No saved snapshot': 'சேமித்த தரவு இல்லை',
 'Demo validation failed': 'மாதிரித் தரவுச் சரிபார்ப்பு தோல்வியடைந்தது',
 'Source: {origin}': 'தரவு மூலம்: {origin}', 'Sample': 'மாதிரி', 'Uploaded': 'பதிவேற்றப்பட்டது',
 'No active dataset': 'நடப்புத் தரவு இல்லை', 'Unknown': 'தெரியவில்லை',
 'Validated records: {n}': 'சரிபார்க்கப்பட்ட பதிவுகள்: {n}',
 'Buyer records: {n}. Count covers the full buyer dataset.': 'வாங்குபவர் பதிவுகள்: {n}. இது முழு வாங்குபவர் தரவிற்கான எண்ணிக்கை.',
 'Active agriculture records: {n}': 'நடப்பு வேளாண் பதிவுகள்: {n}',
 'INTELLIGENCE AI · PHASE 6': 'நுண்ணறிவு · கட்டம் 6',
 'Check': 'சோதனை', 'Count': 'எண்ணிக்கை', 'record': 'பதிவு', 'column': 'நெடுவரிசை', 'value': 'மதிப்பு', 'issue': 'பிழை',
 'Crop name': 'பயிர்ப் பெயர்', 'Buyer name': 'வாங்குபவர் பெயர்',
 'File': 'கோப்பு', 'Origin': 'மூலம்', 'Validated at': 'சரிபார்த்த நேரம்', 'Records': 'பதிவுகள்',
 'Crop coverage': 'பயிர் பொருந்துதன்மை', 'crop_in_active_agriculture': 'நடப்பு வேளாண் தரவில் பயிர் உள்ளதா',
 'Input error; check the file structure and selected columns.': 'உள்ளீட்டுப் பிழை; கோப்பின் அமைப்பையும் தேர்ந்தெடுத்த நெடுவரிசைகளையும் சரிபார்க்கவும்.',
 'Values must be finite, numeric and non-negative.': 'மதிப்புகள் வரையறுக்கப்பட்ட பூஜ்ஜியம் அல்லது நேர்மறை எண்களாக இருக்க வேண்டும்.',
 'Blank required text': 'தேவையான உரை விடுபட்டுள்ளது', 'Duplicate identity': 'நகல் அடையாளம்',
 'Select every required field using distinct source columns.': 'தேவையான ஒவ்வொரு புலத்திற்கும் தனித்தனி மூல நெடுவரிசையைத் தேர்ந்தெடுக்கவும்.',
 'Duplicate crop or buyer/crop identities are not allowed.': 'நகல் பயிர் அல்லது வாங்குபவர் மற்றும் பயிர் பதிவுகள் அனுமதிக்கப்படாது.',
 'Dataset has no records.': 'தரவுத் தொகுப்பில் பதிவுகள் இல்லை.',
 'Unmapped extra columns are excluded from calculations.': 'பொருத்தப்படாத கூடுதல் நெடுவரிசைகள் கணக்கீட்டில் சேர்க்கப்படாது.',
 'Unable to save or restore the local snapshot.': 'உள்ளூர் தரவைச் சேமிக்க அல்லது மீட்டெடுக்க முடியவில்லை.',
 'Calculated currency exceeds the supported finite range.': 'கணக்கிட்ட பண மதிப்பு ஆதரிக்கப்படும் வரம்பை மீறுகிறது.',
 'Invalid planning thresholds; use a positive age and a percentage above zero and at most 100.': 'தவறான திட்டமிடும் வரம்புகள்; நேர்மறை நாட்களையும் பூஜ்ஜியத்தை விட அதிகமாகவும் 100 ஐ மீறாத சதவீதத்தையும் பயன்படுத்தவும்.',
 'Large-surplus threshold: {ratio}%; harvest-age review threshold: {days} days.': 'அதிக உபரி வரம்பு: {ratio}%; அறுவடை வயது பரிசீலனை வரம்பு: {days} நாட்கள்.',
 'For surplus crops: review score = large-surplus flag + age-review flag. 0 = Low; 1 = Moderate; 2 = High. Crops without surplus show No surplus, with age review shown independently.': 'உபரி உள்ள பயிர்களுக்கு: பரிசீலனை மதிப்பெண் = அதிக உபரி அறிகுறி + வயது அறிகுறி. 0 = குறைவு; 1 = மிதம்; 2 = அதிகம். உபரி இல்லாத பயிர்களுக்கு வயது அறிகுறி தனியாகக் காட்டப்படும்.',
 'Surplus {surplus} kg; shortage {shortage} kg.': 'உபரி {surplus} கிலோ; பற்றாக்குறை {shortage} கிலோ.',
 'Available {available} kg − estimated demand {demand} kg gives {surplus} kg potential surplus and {shortage} kg shortage.': 'இருப்பு {available} கிலோ − மதிப்பிடப்பட்ட தேவை {demand} கிலோ: சாத்தியமான உபரி {surplus} கிலோ; பற்றாக்குறை {shortage} கிலோ.',
 'Surplus share {ratio}%; review score {score}/2; level {level}.': 'உபரி விகிதம் {ratio}%; பரிசீலனை மதிப்பெண் {score}/2; நிலை {level}.',
 'Potential surplus: {crop}, {quantity} kg.': 'சாத்தியமான உபரி: {crop}, {quantity} கிலோ.',
 'Remaining surplus {before} kg; request {request} kg; potential match {matched} kg; remaining {after} kg.': 'மீதமுள்ள உபரி {before} கிலோ; தேவை {request} கிலோ; சாத்தியமான பொருத்தம் {matched} கிலோ; மீதி {after} கிலோ.',
 'Unknown crop; no surplus can be allocated.': 'தரவிலில்லாத பயிர்; உபரியை ஒதுக்க முடியாது.',
 'Buyer request is zero; no allocation or trip is assumed.': 'வாங்குபவர் தேவை பூஜ்ஜியம்; ஒதுக்கீடு அல்லது பயணம் இல்லை.',
 'No positive crop surplus is available.': 'பயிருக்கு நேர்மறை உபரி இல்லை.',
 'Earlier buyer rows consumed this crop surplus.': 'முந்தைய வாங்குபவர் பதிவுகள் இந்தப் பயிரின் உபரியைப் பயன்படுத்திவிட்டன.',
 '{quantity} kg × ₹{price} − ₹{transport} transport = ₹{result}.': '{quantity} கிலோ × ₹{price} − போக்குவரத்து ₹{transport} = ₹{result}.',
 '{quantity} kg · ₹{amount} — unmatched reference before costs, not revenue.': '{quantity} கிலோ · ₹{amount} — பொருந்தாத உபரியின் செலவுக்கு முந்தைய குறிப்பு; வருவாய் அல்ல.',
 'No allocations': 'ஒதுக்கீடுகள் இல்லை', 'kg': 'கிலோ', 'days': 'நாட்கள்',
 'Restaurant': 'உணவகம்', 'Hostel': 'விடுதி', 'Retailer': 'சில்லறை விற்பனையாளர்',
 'Tomatoes': 'தக்காளி', 'Onions': 'வெங்காயம்', 'Carrots': 'கேரட்',
 'Green Leaf Restaurant': 'கிரீன் லீஃப் உணவகம்', 'City Hostel': 'சிட்டி விடுதி', 'Fresh Basket Market': 'ஃப்ரெஷ் பாஸ்கெட் சந்தை',
 'Ask a question about the active data': 'நடப்புத் தரவைப் பற்றிக் கேளுங்கள்', 'Question': 'கேள்வி',
 'Assistant scope': 'உதவியாளர் வரம்பு', 'Ask': 'கேள்', 'Clear conversation': 'உரையாடலை அழி',
 'Evidence from active calculations': 'நடப்புக் கணக்கீடுகளின் ஆதாரம்', 'Calculation sources': 'கணக்கீட்டு மூலங்கள்',
 'Download assistant conversation': 'உதவியாளர் உரையாடலைப் பதிவிறக்கு',
 'Rule-based assistant; no external model or live information is used.': 'விதி அடிப்படையிலான உதவியாளர்; வெளி மாதிரி அல்லது நேரடித் தகவல் பயன்படுத்தப்படாது.',
 'Answers are recalculated from current active data and planning rules on every rerun.': 'ஒவ்வொரு புதுப்பிப்பிலும் நடப்புத் தரவு மற்றும் திட்டமிடும் விதிகளிலிருந்து பதில்கள் மீண்டும் கணக்கிடப்படும்.',
 'Which crop should I prioritise?': 'எந்தப் பயிருக்கு முன்னுரிமை கொடுக்க வேண்டும்?',
 'Show surplus and shortages': 'உபரி மற்றும் பற்றாக்குறையைக் காட்டு',
 'Explain the buyer matches': 'வாங்குபவர் பொருத்தங்களை விளக்கு',
 'Explain the returns after transport': 'போக்குவரத்துக்குப் பிந்தைய வருவாயை விளக்கு',
 'Explain the risk rules': 'அபாயப் பரிசீலனை விதிகளை விளக்கு',
 'Suggested question': 'பரிந்துரைக்கப்படும் கேள்வி', 'Use suggested question': 'பரிந்துரைக்கப்பட்ட கேள்வியைக் கேள்',
 'Load validated agriculture data before asking the assistant.': 'உதவியாளரிடம் கேட்பதற்கு முன் சரிபார்க்கப்பட்ட வேளாண் தரவை ஏற்றவும்.',
 'Buyer data is not active; load buyer opportunities to calculate matches and returns.': 'வாங்குபவர் தரவு இல்லை; பொருத்தங்களையும் வருவாயையும் கணக்கிட வாங்குபவர் வாய்ப்புகளை ஏற்றவும்.',
 'I can explain priorities, surplus, shortages, review rules, buyer matches and estimated returns from active data.': 'நடப்புத் தரவிலிருந்து முன்னுரிமை, உபரி, பற்றாக்குறை, பரிசீலனை விதிகள், வாங்குபவர் பொருத்தம் மற்றும் மதிப்பிடப்பட்ட வருவாய் ஆகியவற்றை விளக்க முடியும்.',
 'No live prices, weather, confirmed orders, model forecasts or actual profit are available.': 'நேரடிச் சந்தை விலை, வானிலை, உறுதியான ஆர்டர்கள், மாதிரி முன்னறிவிப்புகள் அல்லது உண்மையான லாபம் கிடைக்கவில்லை.',
 'Prioritise {crop} for surplus-selling review: {surplus} kg potential surplus.': 'உபரி விற்பனைப் பரிசீலனையில் {crop} பயிருக்கு முன்னுரிமை கொடுக்கவும்: சாத்தியமான உபரி {surplus} கிலோ.',
 'Rank uses largest positive surplus, then older harvest, then crop name; it is not a perishability or profit forecast.': 'முன்னுரிமை அதிக நேர்மறை உபரி, அடுத்து அறுவடை வயது, அடுத்து பயிர்ப் பெயர் ஆகியவற்றின் அடிப்படையில் அமையும்; இது அழுகல் அல்லது லாப முன்னறிவிப்பு அல்ல.',
 '{crop}: {matched} kg potentially matched; {unmatched} kg still unmatched.': '{crop}: {matched} கிலோ சாத்தியமாகப் பொருந்தியுள்ளது; {unmatched} கிலோ இன்னும் பொருந்தவில்லை.',
 'Combined estimated return after buyer transport: ₹{amount}.': 'வாங்குபவர் போக்குவரத்துக்குப் பிந்தைய மொத்த மதிப்பிடப்பட்ட வருவாய்: ₹{amount}.',
 'Buyer gross ₹{gross} − transport ₹{transport} = estimated return ₹{result}.': 'வாங்குபவர் மொத்த வருவாய் ₹{gross} − போக்குவரத்து ₹{transport} = மதிப்பிடப்பட்ட வருவாய் ₹{result}.',
 'Same matched quantity market reference: ₹{reference}, before unknown market transport and other costs.': 'அதே பொருந்திய அளவிற்கான சந்தைக் குறிப்பு: ₹{reference}; தெரியாத சந்தைப் போக்குவரத்து மற்றும் பிற செலவுகளுக்கு முன்.',
 'Surplus {surplus} kg and shortages {shortage} kg are summed separately.': 'உபரி {surplus} கிலோ மற்றும் பற்றாக்குறை {shortage} கிலோ தனித்தனியாகக் கூட்டப்படுகின்றன.',
 'Use the scope selector to choose a specific active crop.': 'குறிப்பிட்ட நடப்புப் பயிரைத் தேர்ந்தெடுக்க வரம்புத் தேர்வைப் பயன்படுத்தவும்.',
 'Question {n}': 'கேள்வி {n}', 'Answer': 'பதில்', 'No question yet': 'இன்னும் கேள்வி இல்லை',
 'Overview calculations': 'சுருக்கக் கணக்கீடுகள்', 'Priority and risk calculations': 'முன்னுரிமை மற்றும் அபாயக் கணக்கீடுகள்',
 'Buyer allocation calculations': 'வாங்குபவர் ஒதுக்கீட்டுக் கணக்கீடுகள்', 'Financial calculations': 'நிதிக் கணக்கீடுகள்',
 'This crop is not in the active agriculture dataset.': 'இந்தப் பயிர் நடப்பு வேளாண் தரவில் இல்லை.',
}
LABELS.update(EXTRA)
from .business_labels import LABELS as BUSINESS_LABELS
LABELS.update(BUSINESS_LABELS)
from .ops_labels import LABELS as OPS_LABELS
LABELS.update(OPS_LABELS)
# Remove Latin abbreviations from Tamil-owned labels.
LABELS = {key: value.replace('CSV', 'தரவுக் கோப்பு').replace('AI', 'நுண்ணறிவு') for key,value in LABELS.items()}
for source,(en,ta) in PAIRED.items():
    LABELS[source] = ta

import re
TAMIL = re.compile(r'[\u0b80-\u0bff]')
LATIN = re.compile(r'[A-Za-z]')
REVERSE = {value:key for key,value in LABELS.items() if not TAMIL.search(key)}

def label(text, language):
    text = str(text)
    if language == 'தமிழ்':
        value = LABELS.get(text, text)
        if LATIN.search(re.sub(r'{[^}]*}', '', value)):
            raise KeyError(f'Missing Tamil translation: {text}')
        return value
    if text in PAIRED:
        return PAIRED[text][0]
    if TAMIL.search(text):
        if text in REVERSE:
            return REVERSE[text]
        if text == 'தமிழ்':
            return 'Tamil'
        raise KeyError(f'Missing English translation: {text}')
    return text

class Translator:
    def __init__(self, language='English'):
        self.language = language
        self.identities = {}
    def configure(self, data=None, buyers=None):
        crops = list(data.crop) if data is not None else []
        if buyers is not None: crops += list(buyers.crop)
        names = list(buyers.buyer_name) if buyers is not None else []
        for kind, values in [('Crop',crops),('Buyer',names)]:
            self.identities[kind] = list(dict.fromkeys(str(v).casefold() for v in values))
        return self
    def __call__(self, text, **values):
        return label(text, self.language).format(**values)
    def entity(self, value, kind='Text', n=1):
        text = str(value)
        values = self.identities.get(kind,[])
        if text.casefold() in values: n = values.index(text.casefold()) + 1
        if self.language == 'தமிழ்':
            known = LABELS.get(text)
            if known is None and kind in ('Crop','Buyer'):
                known = next((v for k,v in LABELS.items() if k.casefold()==text.casefold()),None)
            if known and not LATIN.search(known):
                return known
            return text if not any(c.isalpha() and not ('\u0b80' <= c <= '\u0bff') for c in text) else self(f'{kind} {{n}}', n=n)
        known = REVERSE.get(text)
        if known and not TAMIL.search(known):
            return known
        return text if not any(c.isalpha() and not (c.isascii() and c.isalpha()) for c in text) else self(f'{kind} {{n}}', n=n)

LABELS['Planned screen / திட்டமிடப்பட்ட திரை. Detailed workflows will be added in later requested phases.'] = 'திட்டமிடப்பட்ட திரை. விரிவான பணிகள் பிந்தைய கட்டங்களில் சேர்க்கப்படும்.'
LABELS['kg · ₹/kg · days / நாட்கள். Transport is ₹ per buyer trip / போக்குவரத்து ₹ ஒரு பயணத்திற்கு.'] = 'கிலோ · ₹/கிலோ · நாட்கள். போக்குவரத்து: ஒரு பயணத்திற்கான ரூபாய்.'

LABELS['Priority answers rank all active crops; scope applies to the other topics.'] = 'முன்னுரிமைப் பதில்கள் அனைத்து நடப்புப் பயிர்களையும் வரிசைப்படுத்தும்; பிற தலைப்புகளுக்கு வரம்புத் தேர்வு பொருந்தும்.'

LABELS['Upload agriculture CSV'] = 'வேளாண் தரவுக் கோப்பைப் பதிவேற்றவும்'
LABELS['Upload buyers CSV'] = 'வாங்குபவர் தரவுக் கோப்பைப் பதிவேற்றவும்'
LABELS['Download validated CSV'] = 'சரிபார்க்கப்பட்ட தரவைப் பதிவிறக்கவும்'


LABELS.update({
 'Agricultural decision support':'வேளாண் முடிவெடுக்கும் உதவி',
 'Turn agricultural records into practical selling decisions':'வேளாண் பதிவுகளிலிருந்து பயனுள்ள விற்பனை முடிவுகள்',
 'Farmers can have produce available yet face losses without visibility into demand, buyers and returns after transport.':'விளைபொருள் இருந்தும் தேவை, வாங்குபவர்கள் மற்றும் போக்குவரத்துக்குப் பிந்தைய வருவாய் பற்றிய தகவலின்றி விவசாயிகள் இழப்பைச் சந்திக்கலாம்.',
 'Upload records, validate quality, identify potential surplus, preview buyer matches and compare estimated returns.':'பதிவுகளைப் பதிவேற்றி தரத்தைச் சரிபார்த்து, சாத்தியமான உபரியைக் கண்டறிந்து, வாங்குபவர் பொருத்தங்களையும் மதிப்பிடப்பட்ட வருவாயையும் ஒப்பிடவும்.',
 'Get Started':'தொடங்கவும்', 'Download quality-check sample':'தரச் சரிபார்ப்பு மாதிரியைப் பதிவிறக்கவும்',
 'Upload Data → Dashboard → Surplus and Risk → Buyer Matching → Profit Analysis → AI Assistant':'தரவைப் பதிவேற்று → தரவுப் பலகை → உபரி மற்றும் அபாயம் → வாங்குபவர் பொருத்தம் → லாபப் பகுப்பாய்வு → செயற்கை நுண்ணறிவு உதவியாளர்',
 'Skip to main content':'முதன்மை உள்ளடக்கத்திற்குச் செல்லவும்',
})

LABELS.update({
 'Table page':'அட்டவணைப் பக்கம்', 'Page {n} of {pages}':'பக்கம் {n}, மொத்தம் {pages}',
 'Showing records {first}–{last} of {total}.':'பதிவுகள் {first}–{last}; மொத்தம் {total}.',
})
