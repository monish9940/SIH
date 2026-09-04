import React, { useState } from 'react';
import { ShieldCheck, AlertTriangle, ChevronDown, ChevronUp, CheckCircle, Info, Filter } from 'lucide-react';

const guidelineSections = [
  {
    id: 'sec-1',
    num: '01',
    title: 'General Requirements',
    summary: 'Basic requirements for pre-packaged commodities.',
    bullets: [
      'A package intended for retail sale should carry the declarations required under the applicable Legal Metrology framework in a clear and conspicuous manner.',
      'Declarations should be clear and readable.',
      'Required information should be placed on the package or securely affixed label, as applicable.',
      'Information should not be presented in a misleading manner.',
      'Applicable commodity-specific requirements must also be considered.'
    ],
    tip: 'The system can use image and OCR analysis to identify whether expected declarations appear on the package.'
  },
  {
    id: 'sec-2',
    num: '02',
    title: 'Mandatory Package Declarations',
    summary: 'Core information required on retail packages.',
    bullets: [
      'Name and address of the manufacturer, packer, or importer.',
      'Common or generic name of the commodity contained in the package.',
      'Net quantity in standard units of weight, measure, or number.',
      'Maximum Retail Price (MRP) inclusive of all taxes.',
      'Month and year of manufacture or packing.',
      'Consumer care contact details including name, address, telephone number, and email.'
    ],
    tip: 'Ensure all 6 mandatory declarations are clearly printed on the Principal Display Panel.'
  },
  {
    id: 'sec-3',
    num: '03',
    title: 'Manufacturer, Packer & Importer Details',
    summary: 'Identification and address information.',
    bullets: [
      'Every package must declare the full name and complete address of the manufacturer.',
      'Where the manufacturer is not the packer, the packer details must be explicitly mentioned.',
      'For imported packages, the name and complete address of the importer must be declared.'
    ],
    tip: 'Address declarations must include PIN code and identifiable landmark/street details.'
  },
  {
    id: 'sec-4',
    num: '04',
    title: 'Net Quantity',
    summary: 'Declaration of quantity contained in the package.',
    bullets: [
      'Declared in standard units of mass (g, kg), volume (ml, L), length (m), or count (N).',
      'The symbol used for unit of measurement must conform to statutory SI guidelines (e.g. kg, not Kg or KG).',
      'No qualifier should be added to the net quantity declaration (e.g. avoid "approximate 1 kg").'
    ],
    tip: 'Check that standard units use correct lowercase symbols without full stops.'
  },
  {
    id: 'sec-5',
    num: '05',
    title: 'Retail Sale Price / MRP',
    summary: 'Retail price declaration requirements.',
    bullets: [
      'MRP must be printed as "Maximum Retail Price ₹ xx.xx (incl. of all taxes)".',
      'Unit Sale Price (USP) must be declared where required (e.g., ₹ per gram or ₹ per ml).',
      'Price smudging, overwriting, or sticker-over-sticker price masking is illegal.'
    ],
    tip: 'Verify that the price includes the rupee symbol ₹ and explicit tax declaration.'
  },
  {
    id: 'sec-6',
    num: '06',
    title: 'Date & Manufacturing Information',
    summary: 'Month and year declarations.',
    bullets: [
      'Month and year in which the commodity was manufactured, packed, or imported.',
      'Format should be MM/YYYY or Month YYYY.',
      'Best Before / Expiry date declaration is required for perishable or food products.'
    ],
    tip: 'Date formats must strictly follow statutory numerical or month name guidelines.'
  },
  {
    id: 'sec-7',
    num: '07',
    title: 'Consumer Care Details',
    summary: 'Consumer contact information.',
    bullets: [
      'Name, address, telephone number, and email address of the person or office that can be contacted in case of consumer complaints.',
      'Toll-free hotline or customer care phone number must be operational.'
    ],
    tip: 'Missing email or telephone in consumer care box constitutes a statutory violation.'
  },
  {
    id: 'sec-8',
    num: '08',
    title: 'Standard Pack Sizes',
    summary: 'Applicable prescribed standard quantities.',
    bullets: [
      'Certain specified commodities (such as tea, biscuits, milk, oil) must only be packaged in prescribed standard quantities specified under Schedule II.',
      'Non-standard pack sizes require explicit statutory authorization or exemption.'
    ],
    tip: 'Check commodity type against scheduled standard sizes to ensure compliance.'
  }
];

const Guidelines = () => {
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [expandedSection, setExpandedSection] = useState('sec-1');

  const toggleSection = (id) => {
    setExpandedSection(expandedSection === id ? null : id);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Title Header */}
      <div className="text-center space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-amber-600">COMPLIANCE REFERENCE</p>
        <h1 className="text-3xl font-extrabold text-slate-900">Packaged Commodity Guidelines</h1>
        <p className="text-xs text-slate-500 max-w-2xl mx-auto leading-relaxed">
          Understand the key declarations and compliance requirements applicable to pre-packaged commodities under the Legal Metrology framework.
        </p>
      </div>

      {/* Important Compliance Notice Box */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r text-xs text-amber-900 space-y-1">
        <div className="flex items-center gap-2 font-bold text-amber-900">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>Important Compliance Notice</span>
        </div>
        <p>
          These guidelines are provided as a quick reference for users of the Compliance Checker. They are not a substitute for the Legal Metrology Act, 2009, the Legal Metrology (Packaged Commodities) Rules, 2011, or subsequent notifications and amendments. In case of any conflict, the latest applicable official notification/rule shall prevail.
        </p>
      </div>

      {/* Quick Compliance Checklist Cards */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Filter className="w-4 h-4 text-navy-900" />
          Quick Compliance Checklist
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          {[
            { id: 'ALL', label: 'All Requirements' },
            { id: 'MANUFACTURER', label: 'Manufacturer / Packer / Importer' },
            { id: 'QUANTITY', label: 'Commodity & Net Quantity' },
            { id: 'PRICE', label: 'Retail Sale Price' },
            { id: 'CARE', label: 'Consumer Care' }
          ].slice(1).map((cat, idx) => (
            <button
              key={idx}
              onClick={() => setActiveCategory(cat.id)}
              className={`p-4 rounded-lg border text-center transition-all text-xs font-bold ${
                activeCategory === cat.id
                  ? 'bg-navy-900 text-white border-navy-900 shadow-md'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-navy-900 hover:bg-slate-50'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Guideline Accordion Sections */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-slate-900 border-b border-slate-200 pb-3">
          Guideline Sections
        </h2>

        <div className="space-y-3">
          {guidelineSections.map((sec) => {
            const isExpanded = expandedSection === sec.id;
            return (
              <div key={sec.id} className="border border-slate-200 rounded-lg overflow-hidden transition-all">
                <button
                  onClick={() => toggleSection(sec.id)}
                  className="w-full bg-slate-50 hover:bg-slate-100 p-4 flex justify-between items-center text-left gap-4"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 bg-navy-900 text-white text-xs font-bold rounded flex items-center justify-center shrink-0">
                      {sec.num}
                    </span>
                    <div>
                      <h3 className="text-xs font-bold text-slate-900">{sec.title}</h3>
                      <p className="text-[11px] text-slate-500">{sec.summary}</p>
                    </div>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-slate-500 shrink-0" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
                  )}
                </button>

                {isExpanded && (
                  <div className="p-4 bg-white border-t border-slate-200 space-y-4 text-xs">
                    <ul className="space-y-2">
                      {sec.bullets.map((bullet, bIdx) => (
                        <li key={bIdx} className="flex items-start gap-2.5 text-slate-700">
                          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                          <span className="leading-relaxed">{bullet}</span>
                        </li>
                      ))}
                    </ul>

                    {sec.tip && (
                      <div className="bg-blue-50 border border-blue-200 rounded p-3 text-blue-900 flex items-start gap-2 text-xs">
                        <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold">Compliance Checker Tip: </span>
                          <span>{sec.tip}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Guidelines;
