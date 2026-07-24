import { Route, Routes } from "react-router-dom";
import DocumentTitle from "./components/DocumentTitle.jsx";
import Layout from "./components/Layout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Account from "./pages/Account.jsx";
import Assistant from "./pages/Assistant.jsx";
import Booking from "./pages/Booking.jsx";
import DoctorDetail from "./pages/DoctorDetail.jsx";
import Doctors from "./pages/Doctors.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";

function Placeholder({ name }) {
  return <div className="p-lg text-on-surface-variant">{name}</div>;
}

export default function App() {
  return (
    <>
      <DocumentTitle />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/doctors" element={<Doctors />} />
          <Route path="/doctors/:id" element={<DoctorDetail />} />
          <Route path="/booking" element={<Booking />} />
          <Route path="/booking/:doctorId" element={<Booking />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route
            path="/account"
            element={
              <ProtectedRoute>
                <Account />
              </ProtectedRoute>
            }
          />
          <Route path="/doctor/today" element={<Placeholder name="DoctorToday" />} />
          <Route path="/doctor/schedule" element={<Placeholder name="DoctorSchedule" />} />
          <Route path="/admin/filials" element={<Placeholder name="AdminFilials" />} />
          <Route path="/admin/departments" element={<Placeholder name="AdminDepartments" />} />
          <Route path="/admin/doctors" element={<Placeholder name="AdminDoctors" />} />
          <Route path="/admin/reports" element={<Placeholder name="AdminReports" />} />
          <Route path="*" element={<Placeholder name="NotFound" />} />
        </Route>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
      </Routes>
    </>
  );
}
