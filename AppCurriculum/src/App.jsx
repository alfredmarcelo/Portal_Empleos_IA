import "./App.css";
import Main from "./FrontPanel/main.jsx";
import Header from "./FrontPanel/header.jsx";
import { ThemeProvider } from "./FrontPanel/ThemeContext";

function App() {
  return (
    <ThemeProvider>
      <Header />
      <Main />
    </ThemeProvider>
  );
}

export default App;

