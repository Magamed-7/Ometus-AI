import { Route, Routes } from "react-router-dom";
import DocumentTitle from "./components/DocumentTitle.jsx";

function Placeholder({ name }) {
  return <div className="p-lg text-on-surface-variant">{name}</div>;
}

export default function App() {
  return (
    <>
      <DocumentTitle />
      <Routes>
      <Route path="/" element={<Placeholder name="Home" />} />
      <Route path="/doctors" element={<Placeholder name="Doctors" />} />
      <Route path="/doctors/:id" element={<Placeholder name="DoctorDetail" />} />
      <Route path="/booking" element={<Placeholder name="Booking" />} />
      <Route path="/booking/:doctorId" element={<Placeholder name="Booking" />} />
      <Route path="/assistant" element={<Placeholder name="Assistant" />} />
      <Route path="/account" element={<Placeholder name="Account" />} />
      <Route path="/login" element={<Placeholder name="Login" />} />
      <Route path="/register" element={<Placeholder name="Register" />} />
      <Route path="/verify-email" element={<Placeholder name="VerifyEmail" />} />
      <Route path="/doctor/today" element={<Placeholder name="DoctorToday" />} />
      <Route path="/doctor/schedule" element={<Placeholder name="DoctorSchedule" />} />
      <Route path="/admin/filials" element={<Placeholder name="AdminFilials" />} />
      <Route path="/admin/departments" element={<Placeholder name="AdminDepartments" />} />
      <Route path="/admin/doctors" element={<Placeholder name="AdminDoctors" />} />
      <Route path="/admin/reports" element={<Placeholder name="AdminReports" />} />
        <Route path="*" element={<Placeholder name="NotFound" />} />
      </Routes>
    </>
  );
}
