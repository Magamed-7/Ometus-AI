import { Navigate, Route, Routes } from "react-router-dom";
import DocumentTitle from "./components/DocumentTitle.jsx";
import Layout from "./components/Layout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import RoleRoute from "./components/RoleRoute.jsx";
import About from "./pages/About.jsx";
import Account from "./pages/Account.jsx";
import AdminAppointments from "./pages/admin/AdminAppointments.jsx";
import AdminDepartments from "./pages/admin/AdminDepartments.jsx";
import AdminDoctors from "./pages/admin/AdminDoctors.jsx";
import AdminFilials from "./pages/admin/AdminFilials.jsx";
import AdminReports from "./pages/admin/AdminReports.jsx";
import AdminShell from "./pages/admin/AdminShell.jsx";
import Assistant from "./pages/Assistant.jsx";
import Booking from "./pages/Booking.jsx";
import DoctorDetail from "./pages/DoctorDetail.jsx";
import Doctors from "./pages/Doctors.jsx";
import DoctorSchedule from "./pages/doctor/DoctorSchedule.jsx";
import DoctorToday from "./pages/doctor/DoctorToday.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import NotFound from "./pages/NotFound.jsx";
import Register from "./pages/Register.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";

export default function App() {
  return (
    <>
      <DocumentTitle />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
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
          <Route
            path="/doctor/today"
            element={
              <RoleRoute role="doctor">
                <DoctorToday />
              </RoleRoute>
            }
          />
          <Route
            path="/doctor/schedule"
            element={
              <RoleRoute role="doctor">
                <DoctorSchedule />
              </RoleRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <RoleRoute role="admin">
                <AdminShell />
              </RoleRoute>
            }
          >
            <Route index element={<Navigate to="/admin/filials" replace />} />
            <Route path="filials" element={<AdminFilials />} />
            <Route path="departments" element={<AdminDepartments />} />
            <Route path="doctors" element={<AdminDoctors />} />
            <Route path="appointments" element={<AdminAppointments />} />
            <Route path="reports" element={<AdminReports />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
      </Routes>
    </>
  );
}
