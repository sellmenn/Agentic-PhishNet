import HighlightedText from "./HighlightedText";

export default function EmailViewer({ email }) {
  if (!email) return <div className="flex-1 flex items-center justify-center text-gray-500">Select an email</div>;

  return (
    <div className="flex-1 p-6 overflow-y-auto bg-panel">
      <div className="mb-4">
        <h1 className="font-bold text-xl text-gray-100">{email.subject}</h1>
        <p className="text-sm text-gray-400 mb-4">{email.sender}</p>
        <div className="flex gap-2">
          <span className="badge badge-green">Verified DKIM</span>
          <span className="badge badge-yellow">External</span>
          {email.type === "phishing" && <span className="badge badge-red">Agent flagged</span>}
        </div>
      </div>
      {email.type === "phishing" ? (
        <div className="space-y-4">
          <HighlightedText text={email.body} highlights={email.highlights} />
          <div className="rounded-lg border border-red-400/30 bg-red-900/20 p-3 text-sm text-red-200">
            This email was classified as <strong>phishing</strong>. Review highlights and consider quarantining.
          </div>
        </div>
      ) : (
        <p className="text-gray-200">{email.body}</p>
      )}
    </div>
  );
}
