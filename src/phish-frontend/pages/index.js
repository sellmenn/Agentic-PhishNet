import { useEffect, useState } from "react";
import EmailList from "@/components/EmailList";
import EmailViewer from "@/components/EmailViewer";
import Layout from "@/components/Layout";
import { subscribeToNewEmails } from "@/utils/mockEvents";

export default function Inbox() {
  const [emails, setEmails] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    const unsubscribe = subscribeToNewEmails((email) => {
      if (email.type === "phishing") {
        window.dispatchEvent(new CustomEvent("spamEmail", { detail: email }));
      } else {
        setEmails((prev) => [email, ...prev]);
      }
    });
    return unsubscribe;
  }, []);

  return (
    <Layout selectedEmail={selected}>
      <div className="flex">
        <EmailList emails={emails} onSelect={setSelected} />
        <EmailViewer email={selected} />
      </div>
    </Layout>
  );
}
