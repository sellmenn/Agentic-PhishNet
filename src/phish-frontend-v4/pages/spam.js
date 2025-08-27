import { useEffect, useState } from "react";
import EmailList from "@/components/EmailList";
import EmailViewer from "@/components/EmailViewer";
import Layout from "@/components/Layout";

export default function Spam() {
  const [spamEmails, setSpamEmails] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    const handler = (e) => setSpamEmails((prev) => [e.detail, ...prev]);
    window.addEventListener("spamEmail", handler);
    return () => window.removeEventListener("spamEmail", handler);
  }, []);

  return (
    <Layout selectedEmail={selected}>
      <div className="flex">
        <EmailList emails={spamEmails} onSelect={setSelected} />
        <EmailViewer email={selected} />
      </div>
    </Layout>
  );
}
