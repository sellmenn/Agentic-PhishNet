import TopBar from "./TopBar";
import Sidebar from "./Sidebar";
import RightPanel from "./RightPanel";

export default function Layout({ children, selectedEmail }) {
  return (
    <div className="min-h-screen text-gray-200">
      <TopBar />
      <div className="flex">
        <Sidebar />
        <div className="flex-1">{children}</div>
        <RightPanel email={selectedEmail} />
      </div>
    </div>
  );
}
