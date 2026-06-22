const POWERBI_EMBED_URL =
  'https://app.powerbi.com/reportEmbed?reportId=REMPLACE_PAR_TON_REPORT_ID&autoAuth=true&ctid=REMPLACE_PAR_TON_TENANT_ID';

export default function PowerBIDashboard() {
  return (
    <div className="flex flex-col h-full gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Dashboard Power BI</h1>
        <p className="text-sm text-gray-500 mt-1">Indicateurs ESG — Vue consolidée</p>
      </div>

      <div className="flex-1 rounded-xl overflow-hidden border border-gray-200 shadow-sm bg-white min-h-[600px]">
        <iframe
          title="Dashboard ESG Power BI"
          src={POWERBI_EMBED_URL}
          width="100%"
          height="100%"
          style={{ minHeight: '600px', border: 'none' }}
          allowFullScreen
        />
      </div>
    </div>
  );
}
