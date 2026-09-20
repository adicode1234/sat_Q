export type AppLanguage = 'en' | 'hi' | 'bn';

export const UI_LABELS: Record<string, Record<AppLanguage, string>> = {
  // Navigation & Header
  systemOnline: { en: "System Online", hi: "सिस्टम ऑनलाइन", bn: "সিস্টেম অনলাইন" },
  cloudVisionSetup: { en: "Cloud Vision Setup", hi: "क्लाउड विज़न सेटअप", bn: "ক্লাউড ভিশন সেটআপ" },
  reviewQueue: { en: "Review Queue", hi: "समीक्षा कतार", bn: "পর্যালোচনা সারি" },
  missionControl: { en: "Mission Control", hi: "मिशन नियंत्रण", bn: "মিশন কন্ট্রোল" },
  newAnalysis: { en: "New Analysis", hi: "नया विश्लेषण", bn: "নতুন বিশ্লেষণ" },
  uploadData: { en: "Upload Data", hi: "डेटा अपलोड करें", bn: "ডেটা আপলোড" },
  recentMissions: { en: "Recent Missions", hi: "हालिया मिशन", bn: "সাম্প্রতিক মিশন" },
  analysisTools: { en: "Analysis Tools", hi: "विश्लेषण टूल्स", bn: "বিশ্লেষণ টুলস" },

  // Tools
  vqaTitle: { en: "Ask a Question (VQA)", hi: "प्रश्न पूछें (VQA)", bn: "প্রশ্ন জিজ্ঞাসা করুন (VQA)" },
  vqaDesc: { en: "Natural language queries on satellite imagery", hi: "उपग्रह चित्रों पर प्राकृतिक भाषा में प्रश्न पूछें", bn: "স্যাটেলাইট চিত্রে প্রাকৃতিক ভাষায় অনুসন্ধান" },
  describeTitle: { en: "Describe Image", hi: "छवि का विवरण दें", bn: "চিত্রের বিবরণ দিন" },
  describeDesc: { en: "Get detailed description & insights", hi: "विस्तृत दृश्य विवरण एवं मुख्य इनसाइट्स प्राप्त करें", bn: "বিস্তারিত দৃশ্য বর্ণনা এবং অন্তর্দৃষ্টি পান" },
  landCoverTitle: { en: "Land Cover Detection", hi: "भूमि आवरण पहचान", bn: "ভূমি আচ্ছাদন শনাক্তকরণ" },
  landCoverDesc: { en: "Identify water, vegetation, buildings etc.", hi: "जल, वनस्पति, भवन आदि की पहचान करें", bn: "জল, গাছপালা, ভবন ইত্যাদি চিহ্নিত করুন" },
  changeTitle: { en: "Change Detection", hi: "परिवर्तन का पता लगाएं", bn: "পরিবর্তন শনাক্তকরণ" },
  changeDesc: { en: "Compare before/after images", hi: "पहले और बाद की छवियों की तुलना करें", bn: "আগের এবং পরের চিত্রের তুলনা করুন" },
  fusionTitle: { en: "SAR-Optical Fusion", hi: "SAR-ऑप्टिकल संलयन", bn: "SAR-অপটিক্যাল ফিউশন" },
  fusionDesc: { en: "Multi-sensor analysis", hi: "मल्टी-सेंसर संयुक्त विश्लेषण", bn: "মাল্টি-সেন্সর যৌথ বিশ্লেষণ" },
  reportTitle: { en: "Generate Report", hi: "रिपोर्ट तैयार करें", bn: "প্রতিবেদন তৈরি করুন" },
  reportDesc: { en: "Export findings & insights", hi: "निष्कर्ष एवं रिपोर्ट निर्यात करें", bn: "অনুসন্ধান ও অন্তর্দৃষ্টি রপ্তানি করুন" },

  // Viewer
  viewerTitle: { en: "Satellite Image Viewer", hi: "उपग्रह छवि दर्शक", bn: "স্যাটেলাইট চিত্র প্রদর্শক" },
  view2D: { en: "2D View", hi: "2D दृश्य", bn: "২ডি ভিউ" },
  view3D: { en: "3D Globe (Cesium)", hi: "3D ग्लोब (Cesium)", bn: "৩ডি গ্লোব (Cesium)" },
  analysisReady: { en: "Analysis Ready", hi: "विश्लेषण तैयार", bn: "বিশ্লেষণ প্রস্তুত" },
  all: { en: "All", hi: "सभी", bn: "সব" },
  road: { en: "Road", hi: "सड़क", bn: "সড়ক" },
  building: { en: "Building", hi: "इमारत", bn: "ভবন" },
  forest: { en: "Forest", hi: "वन", bn: "বনভূমি" },
  river: { en: "River", hi: "नदी", bn: "নদী" },
  pond: { en: "Pond", hi: "तालाब", bn: "জলাশয়" },

  // Land Use HUD
  landUseTitle: { en: "LAND USE DISTRIBUTION", hi: "भूमि उपयोग वितरण", bn: "ভূমি ব্যবহারের বিন্যাস" },
  forestLabel: { en: "FOREST", hi: "वन (FOREST)", bn: "বনভূমি (FOREST)" },
  agriLabel: { en: "AGRICULTURAL", hi: "कृषि (AGRICULTURAL)", bn: "কৃষি (AGRICULTURAL)" },
  urbanLabel: { en: "URBAN", hi: "शहरी (URBAN)", bn: "শহুরে (URBAN)" },
  waterLabel: { en: "WATER", hi: "जल (WATER)", bn: "জলভাগ (WATER)" },
  otherLabel: { en: "OTHER", hi: "अन्य (OTHER)", bn: "অন্যান্য (OTHER)" },

  // Executive Analysis Section
  execTitle: { en: "Executive Satellite Interpretation & Analysis", hi: "उपग्रह व्याख्या एवं विश्लेषण रिपोर्ट", bn: "স্যাটেলাইট পর্যবেক্ষণ ও বিশ্লেষণ প্রতিবেদন" },
  analysisBy: { en: "Analysis by", hi: "द्वारा विश्लेषित", bn: "দ্বারা বিশ্লেষিত" },
  sceneDescTitle: { en: "Detailed Scene Description", hi: "विस्तृत दृश्य विवरण", bn: "বিস্তারিত দৃশ্য বর্ণনা" },
  answerTitle: { en: "Answer", hi: "उत्तर", bn: "উত্তর" },
  visibleFeaturesTitle: { en: "Visible Features", hi: "दृश्यमान विशेषताएँ", bn: "দৃশ্যমান বৈশিষ্ট্যসমূহ" },
  cannotEstablishTitle: { en: "Cannot be established", hi: "स्थापित नहीं किया जा सकता", bn: "নির্ধারণ করা সম্ভব নয়" },
  detectedPresentTitle: { en: "Detected in Scene (Present)", hi: "दृश्य में पहचाने गए तत्व (उपस्थित)", bn: "দৃশ্যে চিহ্নিত উপাদান (উপস্থিত)" },
  absentTitle: { en: "Absent / Not Detected", hi: "अनुपस्थित / नहीं पाए गए", bn: "অনুপস্থিত / সনাক্ত করা যায়নি" },
  foundCount: { en: "Found", hi: "मिले", bn: "শনাক্ত" },
  absentCount: { en: "Absent", hi: "अनुपस्थित", bn: "অনুপস্থিত" },
  evidenceSupport: { en: "Evidence support", hi: "साक्ष्य समर्थन", bn: "প্রমাণ সমর্থন" },
  diffMatrixTitle: { en: "Temporal Variance Matrix (T1 Before ➔ T2 After)", hi: "सामयिक परिवर्तन मैट्रिक्स (T1 पहले ➔ T2 बाद)", bn: "সময়ভিত্তিক পরিবর্তন ম্যাট্রিক্স (T1 আগে ➔ T2 পরে)" },
  fusionMatrixTitle: { en: "Cross-Modal Sensor Fusion Matrix (Optical ⟷ SAR)", hi: "सेंसर संलयन मैट्रिक्स (ऑप्टिकल ⟷ SAR)", bn: "ক্রস-মোডাল সেন্সর ফিউশন ম্যাট্রিক্স (অপটিক্যাল ⟷ SAR)" },
  beforeVsAfterBtn: { en: "Before vs After Differences", hi: "पहले बनाम बाद में अंतर", bn: "আগে বনাম পরের পার্থক্য" },
  sceneInventoryBtn: { en: "Scene Feature Inventory", hi: "दृश्य तत्व सूची", bn: "দৃশ্য উপাদান তালিকা" },

  // Mission Insights
  missionInsightsTitle: { en: "Mission Insights", hi: "मिशन इनसाइट्स", bn: "মিশন ইনসাইটস" },
  highPriorityBadge: { en: "High Priority", hi: "उच्च प्राथमिकता", bn: "উচ্চ অগ্রাধিকার" },
  overallAssessment: { en: "Overall Assessment", hi: "समग्र मूल्यांकन", bn: "সামগ্রিক মূল্যায়ন" },
  neuralConfidence: { en: "Neural Detection Confidence", hi: "न्यूरल पहचान विश्वास", bn: "নিউরাল সনাক্তকরণ আস্থা" },
  spectralVerification: { en: "Spectral Claim Verification", hi: "स्पेक्ट्रल दावा सत्यापन", bn: "স্পেকট্রাল দাবি যাচাইকরণ" },
  sensorClarity: { en: "Sensor Usability & Clarity", hi: "सेंसर उपयोगिता एवं स्पष्टता", bn: "সেন্সর ব্যবহারযোগ্যতা ও স্বচ্ছতা" },
  riskLevel: { en: "Risk / Alert Level", hi: "जोखिम / अलर्ट स्तर", bn: "ঝুঁকি / সতর্কতা স্তর" },
  downloadPdf: { en: "Download Report (PDF)", hi: "रिपोर्ट डाउनलोड करें (PDF)", bn: "প্রতিবেদন ডাউনলোড করুন (PDF)" },
  nominal: { en: "Nominal", hi: "सामान्य", bn: "স্বাভাবিক" },
};

// Common satellite terminology glossary for dynamic sentence translation
const PHRASE_DICTIONARY: Array<{ en: RegExp; hi: string; bn: string }> = [
  {
    en: /A winding blue feature, likely a river or water body, traverses the scene vertically\.?/gi,
    hi: "एक घुमावदार नीली आकृति, संभवतः एक नदी या जल निकाय, दृश्य को लंबवत रूप से पार करती है।",
    bn: "একটি বাঁকানো নীল বৈশিষ্ট্য, সম্ভবত একটি নদী বা জলাশয়, দৃশ্যটিকে উল্লম্বভাবে অতিক্রম করেছে।"
  },
  {
    en: /Green areas dominate the background, representing land or vegetation\.?/gi,
    hi: "पृष्ठभूमि में हरे रंग के क्षेत्र प्रमुख हैं, जो भूमि अथवा प्राकृतिक वनस्पति को दर्शाते हैं।",
    bn: "পটভূমিতে সবুজ অঞ্চল প্রাধান্য বিস্তার করেছে, যা জমি বা গাছপালাকে নির্দেশ করে।"
  },
  {
    en: /An orange rectangular patch is visible in the bottom-left quadrant\.?/gi,
    hi: "निचले-बाएं चतुर्थांश में एक नारंगी आयताकार क्षेत्र स्पष्ट दिखाई दे रहा है।",
    bn: "নীচের-বাম চতুর্থাংশে একটি কমলা আয়তাকার অংশ স্পষ্টভাবে দৃশ্যমান।"
  },
  {
    en: /A large white rectangular patch is located on the right side\.?/gi,
    hi: "दाहिनी ओर एक बड़ा सफेद आयताकार ब्लॉक स्थित है।",
    bn: "ডান দিকে একটি বড় সাদা আয়তাকার কাঠামো রয়েছে।"
  },
  {
    en: /The geometric precision of the colored blocks suggests artificial boundaries or map annotations\.?/gi,
    hi: "रंगीन ब्लॉकों की ज्यामितीय सटीकता कृत्रिम सीमाओं अथवा मानचित्र चिह्नों का संकेत देती है।",
    bn: "রঙিন ব্লকগুলির জ্যামিতিক নির্ভুলতা কৃত্রিম সীমানা বা মানচিত্রের চিহ্নের ইঙ্গিত দেয়।"
  },
  {
    en: /The image displays a top-down view of a scene characterized by distinct color blocks and a grainy texture\.?/gi,
    hi: "यह छवि विशिष्ट रंगीन ब्लॉकों और दानेदार बनावट से युक्त एक उपग्रह दृश्य का शीर्ष-स्तरीय (टॉप-डाउन) अवलोकन दर्शाती है।",
    bn: "চিত্রটি স্বতন্ত্র রঙের ব্লক এবং দানাদার টেক্সচার দ্বারা চিহ্নিত একটি স্যাটেলাইট দৃশ্যের ওপরের রূপ প্রদর্শন করে।"
  },
  {
    en: /The majority of the background is a solid green, suggesting vegetated land or a specific terrain type\.?/gi,
    hi: "अधिकांश पृष्ठभूमि ठोस हरे रंग की है, जो वनस्पति आच्छादित भूमि अथवा विशिष्ट भू-भाग का संकेत देती है।",
    bn: "পটভূমির অধিকাংশ অংশ গাঢ় সবুজ, যা গাছপালা ঘেরা জমি বা নির্দিষ্ট ভূ-প্রকৃতির ইঙ্গিত দেয়।"
  },
  {
    en: /A prominent blue, winding feature runs vertically from the top to the bottom, slightly left of center, resembling a river or stream\.?/gi,
    hi: "एक प्रमुख नीला घुमावदार चैनल केंद्र से थोड़ा बाईं ओर ऊपर से नीचे की ओर लंबवत रूप से बहता हुआ दिखाई देता है, जो नदी अथवा जलधारा जैसा दिखता है।",
    bn: "একটি বিশিষ্ট নীল বাঁকানো চ্যানেল কেন্দ্রের কিছুটা বাম দিক দিয়ে ওপর থেকে নীচে উল্লম্বভাবে নেমে এসেছে, যা নদী বা খালের মতো দেখায়।"
  },
  {
    en: /In the bottom-left corner, there is a solid orange-brown rectangular block\.?/gi,
    hi: "निचले-बाएं कोने में एक ठोस नारंगी-भूरा आयताकार ब्लॉक मौजूद है।",
    bn: "নীচের-বাম কোণে একটি সুস্পষ্ট কমলা-বাদামী আয়তাকার ব্লক উপস্থিত।"
  },
  {
    en: /On the right side, a large white or light-grey rectangular block is present\.?/gi,
    hi: "दाहिनी ओर, एक बड़ा सफेद अथवा हल्का भूरा आयताकार ब्लॉक स्थित है।",
    bn: "ডান পাশে একটি বড় সাদা বা হালকা ধূসর আয়তাকার ব্লক রয়েছে।"
  },
  {
    en: /The sharp, geometric edges of the orange and white blocks contrast with the organic, curving shape of the blue feature, indicating that the image may be a stylized map, a segmentation overlay, or a low-resolution processed image rather than a natural optical photograph\.?/gi,
    hi: "नारंगी और सफेद ब्लॉकों के तीखे ज्यामितीय किनारे नीली आकृति की प्राकृतिक घुमावदार बनावट के विपरीत हैं, जो दर्शाता है कि यह छवि प्राकृतिक ऑप्टिकल फोटो के बजाय एक मैप, सेगमेंटेशन ओवरले या प्रोसेस्ड इमेज हो सकती है।",
    bn: "কমলা এবং সাদা ব্লকগুলির তীক্ষ্ণ জ্যামিতিক প্রান্তগুলি নীল বৈশিষ্ট্যের প্রাকৃতিক বাঁকের সাথে বিপরীত, যা নির্দেশ করে যে চিত্রটি প্রাকৃতিক অপটিক্যাল ছবির পরিবর্তে একটি মানচিত্র বা প্রক্রিয়াজাত চিত্র হতে পারে।"
  },
  {
    en: /Multispectral satellite observation confirms a prominent river water channel \(20\.8% coverage\) bordered by contiguous natural vegetation canopy \(53\.4%\) and localized built-up infrastructure \(25\.8%\) with high neural confidence\.?/gi,
    hi: "मल्टीस्पेक्ट्रल उपग्रह अवलोकन उच्च न्यूरल विश्वास के साथ एक प्रमुख नदी जल चैनल (20.8% कवरेज) की पुष्टि करता है, जो निरंतर प्राकृतिक वनस्पति छत्र (53.4%) और स्थानीय निर्मित बुनियादी ढांचे (25.8%) से घिरा हुआ है।",
    bn: "মাল্টিস্পেকট্রাল স্যাটেলাইট পর্যবেক্ষণ উচ্চ নিউরাল আস্থার সাথে একটি প্রধান নদীর জলপথ (২০.৮% এলাকা) নিশ্চিত করে, যা সংলগ্ন প্রাকৃতিক বনভূমি (৫৩.৪%) এবং স্থানীয় জনবসতিপূর্ণ অবকাঠামো (২৫.৮%) দ্বারা বেষ্টিত।"
  },
  {
    en: /Surface water boundaries are stable, delineated, and verified by NDWI spectral absorption\.?/gi,
    hi: "सतही जल सीमाएं स्थिर, सुस्पष्ट और NDWI स्पेक्ट्रल अवशोषण द्वारा सत्यापित हैं।",
    bn: "পৃষ্ঠীয় জলের সীমানা স্থিতিশীল, সুস্পষ্ট এবং NDWI বর্ণালী শোষণ দ্বারা যাচাইকৃত।"
  },
  {
    en: /River water channel clearly delineated across central drainage sector\.?/gi,
    hi: "केंद्रीय जल निकासी क्षेत्र में नदी का जल चैनल स्पष्ट रूप से सीमांकित है।",
    bn: "কেন্দ্রীয় নিষ্কাশন অঞ্চল জুড়ে নদীর জলপথ পরিষ্কারভাবে চিহ্নিত।"
  },
  {
    en: /Confidence: 94% · Primary water channel/gi,
    hi: "विश्वास: 94% · प्राथमिक जल चैनल एवं नदी का फैलाव",
    bn: "আস্থা: ৯৪% · প্রধান জলপথ ও নদীর বিস্তার"
  },
  {
    en: /Confidence: 92% · Natural riparian forest & foliage/gi,
    hi: "विश्वास: 92% · प्राकृतिक तटीय वन एवं हरी वनस्पति",
    bn: "আস্থা: ৯২% · প্রাকৃতিক নদীর তীরবর্তী বন ও সবুজ গাছপালা"
  },
  {
    en: /Confidence: 89% · Urban perimeter & structures/gi,
    hi: "विश्वास: 89% · शहरी परिधि एवं निर्मित संरचनाएं",
    bn: "আস্থা: ৮৯% · শহুরে সীমানা ও নির্মিত কাঠামো"
  },
  {
    en: /Confidence: 90% · Linear transportation corridor/gi,
    hi: "विश्वास: 90% · रैखिक परिवहन गलियारा एवं पहुंच मार्ग",
    bn: "আস্থা: ৯০% · রৈখিক পরিবহন করিডোর ও যোগাযোগ পথ"
  },
  {
    en: /Confidence: 88% · Dielectric microwave signature/gi,
    hi: "विश्वास: 88% · डाई-इलेक्ट्रिक माइक्रोवेव रडार संकेत",
    bn: "আস্থা: ৮৮% · ডাই-ইলেকট্রিক মাইক্রোওয়েভ রাডার সংকেত"
  },
  {
    en: /No anomalous bank overflow or sudden flood runoff observed/gi,
    hi: "तटबंध के बाहर कोई असामान्य बाढ़ या अचानक जलभराव नहीं पाया गया",
    bn: "নদীর কূল ছাপিয়ে কোনো অস্বাভাবিক বন্যা বা আকস্মিক জলপ্লাবন দেখা যায়নি"
  },
  {
    en: /Clear optical visibility; nominal haze \(<4%\)/gi,
    hi: "स्पष्ट ऑप्टिकल दृश्यता; न्यूनतम धुंध (<4%) दर्ज की गई",
    bn: "পরিষ্কার অপটিক্যাল দৃশ্যমানতা; ন্যূনতম কুয়াশা (<৪%) পরিলক্ষিত"
  },
  // Visible Features
  {
    en: /Winding blue linear feature \(river-like\)/gi,
    hi: "घुमावदार नीला रेखीय चैनल (नदी के समान)",
    bn: "বাঁকানো নীল রৈখিক চ্যানেল (নদীর মতো)"
  },
  {
    en: /Green background area/gi,
    hi: "हरा पृष्ठभूमि क्षेत्र (प्राकृतिक वनस्पति छत्र)",
    bn: "সবুজ পটভূমি অঞ্চল (গাছপালা ও বনভূমি)"
  },
  {
    en: /Orange \/ reddish small elements along the edge of the blue feature/gi,
    hi: "नीले चैनल के किनारे स्थित छोटे नारंगी/लाल तत्व (संरचनाएं)",
    bn: "নীল খালের প্রান্তে অবস্থিত ছোট কমলা/লাল উপাদান (কাঠামো)"
  },
  {
    en: /Darker green rectangular \/ triangular shape in upper right/gi,
    hi: "ऊपरी दाएं भाग में गहरा हरा आयताकार/त्रिकोणीय क्षेत्र",
    bn: "উপরের ডানদিকের গাঢ় সবুজ আয়তাকার/ত্রিভুজাকার এলাকা"
  },
  {
    en: /Light blue \/ whitish elongated area at lower left/gi,
    hi: "निचले बाएं भाग में हल्का नीला/सफेद लंबा क्षेत्र",
    bn: "নীচের বামদিকে হালকা নীল/সাদাটে দীর্ঘায়িত এলাকা"
  },
  // Cannot be established
  {
    en: /The real-world nature of the orange elements \(they could be boats, buildings, or artifacts; the low resolution and lack of scale make this impossible to confirm\)/gi,
    hi: "नारंगी तत्वों की वास्तविक प्रकृति (कम रिज़ॉल्यूशन एवं स्केल के अभाव में नाव, इमारत अथवा आर्टिफैक्ट की पुष्टि संभव नहीं)",
    bn: "কমলা উপাদানগুলির প্রকৃত রূপ (কম রেজোলিউশন ও স্কেলের অভাবে নৌকা, ভবন বা কৃত্রিম চিহ্ন নিশ্চিত করা অসম্ভব)"
  },
  {
    en: /The direction of flow of the river/gi,
    hi: "नदी के जल प्रवाह की सटीक दिशा (ऊंचाई मॉडल के बिना निर्धारित नहीं)",
    bn: "নদীর জলের সঠিক প্রবাহের দিক (উচ্চতা ডেটা ছাড়া নির্ধারণ সম্ভব নয়)"
  },
  {
    en: /The specific type of vegetation or land use represented by the green areas/gi,
    hi: "हरे क्षेत्रों द्वारा दर्शायी गई विशिष्ट वनस्पति अथवा कृषि प्रजाति का प्रकार",
    bn: "সবুজ অঞ্চল দ্বারা চিহ্নিত নির্দিষ্ট উদ্ভিদের প্রজাতি বা জমির ব্যবহারের ধরন"
  },
  {
    en: /Any temporal or contextual information \(when or where this was taken\)/gi,
    hi: "समय अथवा भौगोलिक संदर्भ की जानकारी (अधिग्रहण मेटाडेटा के बिना)",
    bn: "সময় বা ভৌগোলিক প্রসঙ্গের তথ্য (অধিগ্রহণ মেটাডেটা ছাড়া)"
  },
  {
    en: /Direction of hydrological flow and subsurface depth cannot be established from 2D imagery\.?/gi,
    hi: "2D उपग्रह छवि से जल प्रवाह की दिशा और उपसतह की गहराई निर्धारित नहीं की जा सकती।",
    bn: "২ডি উপগ্রহ চিত্র থেকে পানির প্রবাহের দিক এবং ভূগর্ভস্থ গভীরতা নির্ধারণ করা সম্ভব নয়।"
  },
  {
    en: /Internal structural integrity of detected settlements requires cadastral survey\.?/gi,
    hi: "पहचाने गए ढांचों की आंतरिक संरचनात्मक स्थिति के लिए ज़मीनी सर्वेक्षण आवश्यक है।",
    bn: "শনাক্তকৃত বসতির অভ্যন্তরীণ কাঠামোগত স্থিতির জন্য সরেজমিন জরিপ প্রয়োজন।"
  },
  {
    en: /Precise vegetative species classification requires hyperspectral calibration\.?/gi,
    hi: "सटीक वनस्पति प्रजाति वर्गीकरण के लिए हाइपरस्पेक्ट्रल कैलिब्रेशन आवश्यक है।",
    bn: "সঠিক উদ্ভিদ প্রজাতি নির্ধারণের জন্য হাইপারস্পেকট্রাল ক্যালিব্রেশন প্রয়োজন।"
  },
  {
    en: /Micro-scale sub-pixel boundaries cannot be established without higher ground sample distance\.?/gi,
    hi: "उच्च रिज़ॉल्यूशन के बिना माइक्रो-स्केल उप-पिक्सेल सीमाएं स्थापित नहीं की जा सकतीं।",
    bn: "উচ্চতর রেজোলিউশন ব্যতীত সাব-পিক্সেল সীমানা নির্ধারণ করা সম্ভব নয়।"
  },
  // Categories & Badges
  { en: /^Water Body \/ River Channel$/gi, hi: "जल निकाय / नदी चैनल", bn: "জলভাগ / নদী প্রণালী" },
  { en: /^Vegetation Canopy$/gi, hi: "प्राकृतिक वनस्पति छत्र", bn: "গাছপালা ও বনভূমি" },
  { en: /^Building & Settlements$/gi, hi: "इमारतें एवं बस्तियाँ", bn: "ভবন ও জনবসতি" },
  { en: /^Road Network & Bridges$/gi, hi: "सड़क नेटवर्क एवं सेतु", bn: "সড়ক ও যোগাযোগ নেটওয়ার্ক" },
  { en: /^Radar Corroborated Surface$/gi, hi: "रडार समर्थित धरातल", bn: "রাডার সমর্থিত পৃষ্ঠভাগ" },
  { en: /^Out-of-Bank Flood Inundation$/gi, hi: "तटबंध के बाहर बाढ़ का फैलाव", bn: "নদীর কূল ছাপানো আকস্মিক বন্যা" },
  { en: /^Atmospheric Occlusion$/gi, hi: "वायुमंडलीय धुंध अथवा बादल", bn: "বায়ুমণ্ডলীয় মেঘ বা কুয়াশা" },
  { en: /^Water$/gi, hi: "जल", bn: "জল" },
  { en: /^Vegetation$/gi, hi: "वनस्पति", bn: "গাছপালা" },
  { en: /^Built-up$/gi, hi: "निर्मित", bn: "নির্মিত" },
  { en: /^Transit$/gi, hi: "परिवहन", bn: "যোগাযোগ" },
  { en: /^Transport$/gi, hi: "परिवहन", bn: "যোগাযোগ" },
  { en: /^Surface$/gi, hi: "धरातल", bn: "পৃষ্ঠভাগ" },
  { en: /^Not Present$/gi, hi: "अनुपस्थित", bn: "অনুপস্থিত" },
  { en: /^Clear$/gi, hi: "स्पष्ट", bn: "পরিষ্কার" },
  { en: /^Detected$/gi, hi: "पहचाना गया", bn: "শনাক্ত" },
];

const DYNAMIC_CACHE: Record<string, string> = {};
const PENDING_KEYS = new Set<string>();

export function getCachedTranslation(text: string, lang: AppLanguage): string | null {
  if (!text || lang === 'en') return text;
  const key = `${lang}:${text.trim()}`;
  return DYNAMIC_CACHE[key] || null;
}

export function setCachedTranslation(text: string, lang: AppLanguage, translated: string) {
  if (!text || !translated || lang === 'en') return;
  const key = `${lang}:${text.trim()}`;
  DYNAMIC_CACHE[key] = translated.trim();
}

export async function fetchDynamicTranslations(texts: string[], lang: AppLanguage): Promise<Record<string, string>> {
  if (!texts || texts.length === 0 || lang === 'en') return {};

  const toFetch: string[] = [];
  const result: Record<string, string> = {};

  for (const t of texts) {
    if (!t || typeof t !== 'string' || !t.trim()) continue;
    const clean = t.trim();
    const key = `${lang}:${clean}`;
    if (DYNAMIC_CACHE[key]) {
      result[clean] = DYNAMIC_CACHE[key];
    } else if (!PENDING_KEYS.has(key)) {
      toFetch.push(clean);
      PENDING_KEYS.add(key);
    }
  }

  if (toFetch.length === 0) return result;

  try {
    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texts: toFetch, target: lang })
    });
    if (res.ok) {
      const data = await res.json();
      const translations: string[] = data.translations || [];
      toFetch.forEach((orig, idx) => {
        const trans = translations[idx] || orig;
        const key = `${lang}:${orig}`;
        DYNAMIC_CACHE[key] = trans;
        PENDING_KEYS.delete(key);
        result[orig] = trans;
      });
    }
  } catch (e) {
    console.warn("Dynamic translation fetch notice:", e);
    toFetch.forEach(orig => PENDING_KEYS.delete(`${lang}:${orig}`));
  }

  return result;
}

/**
 * Translate arbitrary satellite analysis text into target language
 */
export function translateText(text: string, lang: AppLanguage): string {
  if (!text || lang === 'en') return text;

  const cached = getCachedTranslation(text, lang);
  if (cached) return cached;

  let result = text;
  for (const item of PHRASE_DICTIONARY) {
    result = result.replace(item.en, lang === 'hi' ? item.hi : item.bn);
  }

  // Common keywords fallback for untranslated segments
  if (lang === 'hi') {
    result = result
      .replace(/\bwater body\b/gi, "जल निकाय")
      .replace(/\briver channel\b/gi, "नदी चैनल")
      .replace(/\bvegetation canopy\b/gi, "वनस्पति छत्र")
      .replace(/\bbuilt-up area\b/gi, "निर्मित क्षेत्र")
      .replace(/\burban settlement\b/gi, "शहरी बस्ती")
      .replace(/\bhigh confidence\b/gi, "उच्च विश्वसनीयता")
      .replace(/\bdetected in scene\b/gi, "दृश्य में पहचाना गया")
      .replace(/\bnot detected\b/gi, "नहीं पाया गया");
  } else if (lang === 'bn') {
    result = result
      .replace(/\bwater body\b/gi, "জলাশয়")
      .replace(/\briver channel\b/gi, "নদী প্রণালী")
      .replace(/\bvegetation canopy\b/gi, "গাছপালা ও বনভূমি")
      .replace(/\bbuilt-up area\b/gi, "নির্মিত এলাকা")
      .replace(/\burban settlement\b/gi, "শহুরে জনবসতি")
      .replace(/\bhigh confidence\b/gi, "উচ্চ আস্থা")
      .replace(/\bdetected in scene\b/gi, "দৃশ্যে সনাক্ত হয়েছে")
      .replace(/\bnot detected\b/gi, "সনাক্ত করা যায়নি");
  }

  return result;
}

export function t(key: string, lang: AppLanguage): string {
  const item = UI_LABELS[key];
  if (!item) return key;
  return item[lang] || item['en'] || key;
}

export interface HelpTopicInfo {
  title: Record<AppLanguage, string>;
  what: Record<AppLanguage, string>;
  tips: Record<AppLanguage, string[]>;
}

export const HELP_TOPICS: Record<string, HelpTopicInfo> = {
  missionSetup: {
    title: {
      en: "Mission Setup Overview",
      hi: "मिशन सेटअप अवलोकन",
      bn: "মিশন সেটআপ নির্দেশিকা"
    },
    what: {
      en: "Configure and launch a new satellite Earth observation task.",
      hi: "नया उपग्रह पृथ्वी अवलोकन कार्य कॉन्फ़िगर और लॉन्च करें।",
      bn: "নতুন স্যাটেলাইট পৃথিবী পর্যবেক্ষণ কার্য কনফিগার ও চালু করুন।"
    },
    tips: {
      en: [
        "Select an observation mode (Single Image, Optical+SAR, or Before/After).",
        "Upload images in PNG, JPG, or GeoTIFF format (up to 32 MB).",
        "Set the acquisition date and specify your analysis query in plain language."
      ],
      hi: [
        "अवलोकन मोड चुनें (एकल छवि, ऑप्टिकल+SAR, या पहले/बाद में)।",
        "PNG, JPG या GeoTIFF फॉर्मेट में उपग्रह चित्र अपलोड करें (अधिकतम 32 MB)।",
        "अधिग्रहण की तारीख चुनें और सामान्य भाषा में अपना प्रश्न लिखें या बोलें।"
      ],
      bn: [
        "পর্যবেক্ষণ মোড নির্বাচন করুন (একক চিত্র, অপটিক্যাল+SAR, বা আগে/পরে)।",
        "PNG, JPG বা GeoTIFF ফরম্যাটে ছবি আপলোড করুন (সর্বোচ্চ ৩২ MB)।",
        "ছবি তোলার তারিখ দিন এবং সাধারণ ভাষায় আপনার প্রশ্ন টাইপ করুন বা বলুন।"
      ]
    }
  },
  modeSelect: {
    title: {
      en: "Observation Mode Selection",
      hi: "अवलोकन मोड का चयन",
      bn: "পর্যবেক্ষণ মোড নির্বাচন"
    },
    what: {
      en: "Choose how many images and sensors you want to analyze together.",
      hi: "चुनें कि आप एक साथ कितने चित्र और सेंसर का विश्लेषण करना चाहते हैं।",
      bn: "একসাথে কয়টি ছবি ও সেন্সর বিশ্লেষণ করতে চান তা নির্বাচন করুন।"
    },
    tips: {
      en: [
        "Single Image: Detect land-cover, water, roads, and buildings in 1 satellite photo.",
        "Optical + SAR: Combine 1 visible RGB image + 1 radar image to penetrate clouds and verify surface textures.",
        "Before / After: Upload 2 dates of the same area to track floods, construction, or deforestation changes."
      ],
      hi: [
        "Single Image (एकल छवि): 1 उपग्रह फोटो में जल, वनस्पति, सड़क और इमारतों की पहचान।",
        "Optical + SAR: बादलों के पार देखने और सतह की बनावट जांचने के लिए 1 ऑप्टिकल और 1 रडार चित्र जोड़ें।",
        "Before / After: बाढ़, निर्माण या वनों के कटाव की तुलना करने के लिए दो अलग-अलग तारीखों के चित्र डालें।"
      ],
      bn: [
        "Single Image (একক চিত্র): ১টি স্যাটেলাইট ছবিতে নদী, গাছপালা, রাস্তা ও ভবন চিহ্নিত করুন।",
        "Optical + SAR: মেঘ ভেদ করে পৃষ্ঠের আর্দ্রতা ও টেক্সচার যাচাই করতে ১টি অপটিক্যাল ও ১টি রাডার ছবি দিন।",
        "Before / After: বন্যা, অবকাঠামো বা বনভূমির পরিবর্তন মাপতে দুটি আলাদা তারিখের ছবি আপলোড করুন।"
      ]
    }
  },
  imageUpload: {
    title: {
      en: "Satellite Image Upload",
      hi: "उपग्रह चित्र अपलोड",
      bn: "স্যাটেলাইট ছবি আপলোড"
    },
    what: {
      en: "Provide genuine satellite, aerial, or drone orthomosaic imagery.",
      hi: "वास्तविक उपग्रह, हवाई या ड्रोन ऑर्थोमोसेक चित्र अपलोड करें।",
      bn: "প্রকৃত স্যাটেলাইট, আকাশচিত্র বা ড্রোন অর্থোমোসাইক ছবি আপলোড করুন।"
    },
    tips: {
      en: [
        "Formats supported: PNG, JPG, JPEG, and GeoTIFF (.tif / .tiff).",
        "Maximum file size: 32 MB per image.",
        "Works with Sentinel-2, Landsat-8/9, PlanetScope, Google Earth aerial screenshots, or drone maps.",
        "In dual modes, slot 1 is Pre/Optical and slot 2 is Post/SAR."
      ],
      hi: [
        "समर्थित फॉर्मेट: PNG, JPG, JPEG, और GeoTIFF (.tif / .tiff)।",
        "अधिकतम फ़ाइल आकार: प्रति चित्र 32 MB।",
        "Sentinel-2, Landsat-8/9, PlanetScope, गूगल अर्थ स्क्रीनशॉट या ड्रोन मैप के साथ काम करता है।",
        "डुअल मोड में: बायाँ स्लॉट पहले (T1)/ऑप्टिकल के लिए और दायाँ स्लॉट बाद (T2)/SAR के लिए है।"
      ],
      bn: [
        "সমর্থিত ফরম্যাট: PNG, JPG, JPEG, এবং GeoTIFF (.tif / .tiff)।",
        "সর্বোচ্চ ফাইল সাইজ: প্রতি ছবির জন্য ৩২ MB।",
        "Sentinel-2, Landsat-8/9, PlanetScope, গুগল আর্থ বা ড্রোন ম্যাপের সাথে সম্পূর্ণ সামঞ্জস্যপূর্ণ।",
        "ডুয়াল মোডে: বাম দিকের স্লট টি১/অপটিক্যাল এবং ডান দিকের স্লট টি২/SAR এর জন্য।"
      ]
    }
  },
  acquisitionDate: {
    title: {
      en: "Observation Acquisition Date",
      hi: "अधिग्रहण (कैप्चर) की तारीख",
      bn: "ছবি তোলার তারিখ (Acquisition Date)"
    },
    what: {
      en: "Specify the exact date the satellite captured the image.",
      hi: "उपग्रह द्वारा चित्र खींचे जाने की सटीक तारीख चुनें।",
      bn: "স্যাটেলাইট ক্যামেরা দিয়ে ছবিটি ক্যাপচার করার সঠিক তারিখ দিন।"
    },
    tips: {
      en: [
        "Use ISO format: YYYY-MM-DD (e.g. 2026-09-17).",
        "Future dates are prohibited. Historic dates back to 1970 are valid.",
        "For Before/After analysis, entering both dates enables calibrated physical drift calculation."
      ],
      hi: [
        "ISO प्रारूप: YYYY-MM-DD (जैसे: 2026-09-17)।",
        "भविष्य (Future) की तारीख अमान्य है। 1970 से आज तक की तारीख दर्ज करें।",
        "Before/After मोड में दोनों तारीखें दर्ज करें ताकि सटीक समय अंतराल का आकलन हो सके।"
      ],
      bn: [
        "ISO ফরম্যাট ব্যবহার করুন: YYYY-MM-DD (যেমন: 2026-09-17)।",
        "ভবিষ্যতের তারিখ দেওয়া যাবে না। ১৯৭০ থেকে বর্তমান সময় পর্যন্ত তারিখ বৈধ।",
        "Before/After মোডে উভয় তারিখ দিলে সময়ের নিখুঁত পার্থক্যের হিসাব পাওয়া যায়।"
      ]
    }
  },
  sensorModality: {
    title: {
      en: "Sensor Modality Selection",
      hi: "सेंसर मोडैलिटी (प्रकार) का चयन",
      bn: "সেন্সর মডালিটি নির্বাচন"
    },
    what: {
      en: "Declare whether your input represents visible optical light or radar microwaves.",
      hi: "घोषित करें कि आपका चित्र दृश्यमान ऑप्टिकल प्रकाश है या रडार माइक्रोवेव।",
      bn: "আপনার ছবিটি দৃশ্যমান অপটিক্যাল আলো নাকি রাডার মাইক্রোওয়েভ তা চিহ্নিত করুন।"
    },
    tips: {
      en: [
        "Optical (RGB): Standard visible reflection (Sentinel-2, Landsat). Best for colors, rivers, vegetation, urban rooflines.",
        "SAR (Radar): Active microwave backscatter (Sentinel-1, RISAT). Penetrates cloud cover, smoke, and darkness; highlights moisture and structural roughness."
      ],
      hi: [
        "Optical (RGB): दृश्यमान प्रकाश। प्राकृतिक रंगों, नदियों, हरियाली और शहरी मकानों की पहचान के लिए सबसे उपयुक्त।",
        "SAR (Radar): एक्टिव माइक्रोवेव रडार। बादलों और घने कोहरे के पार देखता है तथा जमीन की नमी व कठोर सतहों को स्पष्ट करता है।"
      ],
      bn: [
        "Optical (RGB): সাধারণ দৃশ্যমান আলো। নদী, বনভূমি, শস্যক্ষেত ও শহরের প্রাকৃতিক রঙ দেখতে সেরা।",
        "SAR (Radar): সক্রিয় মাইক্রোওয়েভ রাডার। মেঘ, বৃষ্টি ও রাতের অন্ধকারেও মাটির আর্দ্রতা এবং পৃষ্ঠের অসমতা স্পষ্ট করে।"
      ]
    }
  },
  queryPrompt: {
    title: {
      en: "Analysis Query & Prompt",
      hi: "विश्लेषण प्रश्न एवं निर्देश",
      bn: "বিশ্লেষণ অনুসন্ধান ও প্রশ্ন"
    },
    what: {
      en: "Type or speak your geospatial question in plain English or Hindi.",
      hi: "अंग्रेजी या हिंदी में अपना भू-स्थानिक प्रश्न टाइप करें या बोलें।",
      bn: "সহজ ইংরেজি বা হিন্দিতে আপনার ভূ-স্থানিক প্রশ্নটি লিখুন বা বলুন।"
    },
    tips: {
      en: [
        "Ask about water bodies: 'Where is the river or surface water in this image?'",
        "Ask about urban sprawl: 'Detect buildings and urban infrastructure.'",
        "Ask about environmental health: 'Identify dense vegetation, crops, or forests.'",
        "Ask about infrastructure: 'Highlight roads, bridges, and transport routes.'",
        "Use the Voice Mic button to dictate naturally with your voice."
      ],
      hi: [
        "जल निकायों के लिए: 'Where is the river or surface water in this image?' या 'नदी कहाँ है?'",
        "शहरी बस्तियों के लिए: 'Detect buildings and urban infrastructure' या 'इमारतें खोजें।'",
        "हरियाली के लिए: 'Identify dense vegetation and forests' या 'घने जंगल पहचानें।'",
        "सड़क व पुलों के लिए: 'Highlight roads and transport routes' या 'सड़कें दिखाएं।'",
        "बोलकर इनपुट देने के लिए Voice Mic बटन दबाएँ।"
      ],
      bn: [
        "জলাশয় সংক্রান্ত প্রশ্ন: 'Where is the river or surface water in this image?'",
        "শহুরে কাঠামো সংক্রান্ত প্রশ্ন: 'Detect buildings and urban infrastructure.'",
        "বন ও সবুজায়ন সংক্রান্ত প্রশ্ন: 'Identify dense vegetation and forests.'",
        "যোগাযোগ ব্যবস্থা সংক্রান্ত প্রশ্ন: 'Highlight roads and transport routes.'",
        "মুখে বলে অনুসন্ধান করতে ভয়েস মাইক (Voice Mic) বোতাম ব্যবহার করুন।"
      ]
    }
  },
  voiceMic: {
    title: {
      en: "Voice Dictation (Microphone)",
      hi: "आवाज से बोलें (वॉयस माइक)",
      bn: "ভয়েস মাইক (মাইক্রোফোন)"
    },
    what: {
      en: "Hands-free speech-to-text input in English or Hindi.",
      hi: "अंग्रेजी या हिंदी में बोलकर प्रश्न लिखने की सुविधा।",
      bn: "হাতে টাইপ না করে মুখে বলে প্রশ্ন লেখার সুবিধা।"
    },
    tips: {
      en: [
        "Click the Mic button once to start listening.",
        "Speak clearly into your microphone.",
        "Toggle between '🌐 English' and '🇮🇳 हिन्दी' for accurate recognition.",
        "Click 'Done ✓' or tap the mic again when finished."
      ],
      hi: [
        "सुनना शुरू करने के लिए माइक बटन पर एक बार क्लिक करें।",
        "अपने माइक्रोफ़ोन में स्पष्ट रूप से बोलें।",
        "सटीक पहचान के लिए '🌐 English' और '🇮🇳 हिन्दी' के बीच स्विच करें।",
        "बोलने के बाद 'Done ✓' पर क्लिक करें।"
      ],
      bn: [
        "শুরু করতে একবার মাইক্রোফোন বোতামে ক্লিক করুন।",
        "মাইক্রোফোনে স্পষ্টভাবে প্রশ্নটি বলুন।",
        "সঠিক সনাক্তকরণের জন্য ইংরেজি বা হিন্দিতে রূপান্তর করতে পারেন।",
        "কথা শেষ হলে 'Done ✓' বাটনে ক্লিক করুন।"
      ]
    }
  },
  presetChips: {
    title: {
      en: "Pre-Configured Analysis Chips",
      hi: "पूर्व-कॉन्फ़िगर सुझाव प्रश्न (Chips)",
      bn: "প্রস্তুতকৃত অনুসন্ধান বোতাম (Chips)"
    },
    what: {
      en: "One-click starter queries pre-tuned for high detection accuracy.",
      hi: "उच्च सटीकता के लिए पूर्व-अनुकूलित 1-क्लिक प्रश्न।",
      bn: "উচ্চ নির্ভুলতার জন্য পূর্ব-নির্ধারিত ১-ক্লিক প্রশ্ন।"
    },
    tips: {
      en: [
        "Click any chip to immediately fill the analysis prompt.",
        "🌊 River & Water: Calibrated with NDWI absorption thresholding.",
        "🏠 Buildings & Settlements: Calibrated with morphological contour detection.",
        "🌲 Dense Vegetation: Calibrated with NDVI near-infrared green reflection.",
        "🛣️ Roads & Transit: Calibrated with linear ridge enhancement."
      ],
      hi: [
        "प्रॉम्प्ट में प्रश्न भरने के लिए किसी भी चिप पर सीधे क्लिक करें।",
        "🌊 नदी एवं जल: NDWI अवशोषण थ्रेशोल्ड द्वारा संचालित।",
        "🏠 इमारतें एवं बस्तियाँ: आकृतिक रूपरेखा पहचान द्वारा संचालित।",
        "🌲 घनी वनस्पति: NDVI अवरक्त परावर्तन द्वारा संचालित।",
        "🛣️ सड़कें एवं परिवहन: लीनियर रिज़ संवर्धन द्वारा संचालित।"
      ],
      bn: [
        "ইনপুটে প্রশ্নটি স্বয়ংক্রিয়ভাবে বসাতে যেকোনো চিপে ক্লিক করুন।",
        "🌊 নদী ও জলাশয়: NDWI স্পেকট্রাল শোষণ দ্বারা যাচাইকৃত।",
        "🏠 ভবন ও জনবসতি: কাঠামোগত রূপরেখা সনাক্তকরণ দ্বারা প্রস্তুত।",
        "🌲 বন ও গাছপালা: NDVI নিয়ার-ইনফ্রারেড সবুজায়ন দ্বারা নির্ধারিত।",
        "🛣️ রাস্তা ও যোগাযোগ: রৈখিক পরিবহন পথ সনাক্তকরণ দ্বারা প্রস্তুত।"
      ]
    }
  },
  executeAnalysis: {
    title: {
      en: "Execute Neural Analysis",
      hi: "न्यूरल विश्लेषण निष्पादित करें",
      bn: "নিউরাল विश्लेषण चालू করুন"
    },
    what: {
      en: "Launch the full multi-specialist satellite intelligence pipeline.",
      hi: "संपूर्ण मल्टी-स्पेशलिस्ट उपग्रह खुफिया पाइपलाइन शुरू करें।",
      bn: "সম্পূর্ণ মাল্টি-স্পেশালিস্ট স্যাটেলাইট বিশ্লেষণ পাইপলাইন শুরু করুন।"
    },
    tips: {
      en: [
        "Runs neural spatial detection, spectral physics verification, and land-cover calculations.",
        "Provides 2D View, 3D Cesium Globe, Land Use Distribution HUD, and Executive Analysis.",
        "Strictly adheres to scientific truth verification without fabricated metrics."
      ],
      hi: [
        "न्यूरल डिटेक्शन, स्पेक्ट्रल फिजिक्स सत्यापन और भूमि आवरण गणना शुरू करता है।",
        "2D दृश्य, 3D Cesium ग्लोब, भूमि उपयोग वितरण (HUD) और कार्यकारी रिपोर्ट तैयार करता है।",
        "बिना किसी बनावटी डेटा के सख्त वैज्ञानिक सत्यापन नियमों का पालन करता है।"
      ],
      bn: [
        "নিউরাল সনাক্তকরণ, বর্ণালী নিরীক্ষা ও ভূমি ব্যবহারের হিসাব সম্পন্ন করে।",
        "২ডি ভিউ, ৩ডি Cesium গ্লোব, ল্যান্ড ইউজ ডিস্ট্রিবিউশন HUD এবং বিস্তারিত রিপোর্ট দেয়।",
        "কোনো কাল্পনিক ডেটা ছাড়া সম্পূর্ণ বৈজ্ঞানিক প্রমাণের ভিত্তিতে কাজ করে।"
      ]
    }
  }
};

