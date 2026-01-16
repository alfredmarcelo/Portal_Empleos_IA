import React from "react";
import "./Styles/main.css";
import TextInput from "./Components/TextInput.jsx";
import { MdArrowBackIosNew } from "react-icons/md";
import Map from "./Components/Map.jsx";
import { useTheme } from "./ThemeContext";
import Llm_chat from "./Llm_chat";
import LoadIndicator from "./Components/LoadIndicator.jsx";
import Markdown from 'react-markdown'
import Vacantes_screen from "./Vacantes_screen";
import Apple_map from "./Components/Apple_map";

// Estados de la aplicación
const SCREEN_STATES = {
  INPUT: "input",           // Pantalla inicial de búsqueda
  LOADING: "loading",       // Cargando resultados
  NO_RESULTS: "no_results", // Sin resultados
  RESULTS: "results"        // Mostrando resultados
};

const SCREEN_STATES2 = {
  MAPA: "mapa",
  PAGINA: "pagina",
  OFERTA: "oferta"
}

export default function Main() {
  const { mode } = useTheme();

  // Datos de ejemplo
  const datosEjemplo = [
    {
      puesto: "Desarrollador de Software",
      modalidad: "remoto",
      sueldo: "20,000DOP",
      horario: "8am - 6pm",
      ubicacion: "Santo Domingo",
      descripcion: "descripcion",
      beneficios: "beneficios",
    },
    {
      puesto: "Ingeniero en Redes",
      modalidad: "Presencial",
      sueldo: "20,000DOP",
      horario: "8am - 6pm",
      ubicacion: "Santiago",
      descripcion: "descripcion",
      beneficios: "beneficios",
    },
  ];

  // Estados
  const [inputText, setInputText] = React.useState("");
  const [screenState, setScreenState] = React.useState(SCREEN_STATES.INPUT);
  const [ofertas, setOfertas] = React.useState([]);
  const [IAButton, setIAButton] = React.useState(false);
  const [verPagina, setVerPagina] = React.useState(SCREEN_STATES2.OFERTA);
  const [ofertaSeleccionada, setOfertaSeleccionada] = React.useState(null);
  const [IA_text, setIA_text] = React.useState(null);

  // Handler para iniciar búsqueda
  const handleSearch = () => {
    setScreenState(SCREEN_STATES.LOADING);
    fetchResultados();
  };

  // Fetch de resultados
  const fetchResultados = async () => {
    try {
      const res = await fetch("http://192.168.8.106:8000/pruebas_frontend/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: inputText,
        }),
      });

      console.log(res);
      if (res.ok) {
        const data = await res.json();

        console.log(data);

        if (data.datos === "Vacio") {
          setScreenState(SCREEN_STATES.NO_RESULTS);
        } else {
          setOfertas(data.datos);
          setScreenState(SCREEN_STATES.RESULTS);
        }
      } else {
        setScreenState(SCREEN_STATES.NO_RESULTS);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      setScreenState(SCREEN_STATES.NO_RESULTS);
    }
  };

  const renderOfertas = () => {
    switch (verPagina) {
      case SCREEN_STATES2.OFERTA:
        return <div id="Job-Search-Frame2">
          {ofertas.length === 0
            ? "No hay empleo para mostrar"
            : ofertaSeleccionada ? <Vacantes_screen ofertaSeleccionada={ofertaSeleccionada} /> : "Selecciona una oferta para verla aqui "}
        </div>
      case SCREEN_STATES2.PAGINA:
        return <iframe
          id="Job-Search-Frame2"
          src="https://do.computrabajo.com/empleos-en-distrito-nacional#EF605073D1C3607461373E686DCF3405"
          sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals"
          title="Job Search"
        ></iframe>
      case SCREEN_STATES2.MAPA:
        return (
          <Apple_map />
        );
    }
  }
  const renderContent = () => {
    switch (screenState) {
      case SCREEN_STATES.INPUT:
        return (
          <div id="Text-Input-Section">
            <h1 id="front-panel-title">Que empleo buscas?</h1>
            <TextInput
              inputText={inputText}
              setInputText={setInputText}
              setSearchButton={handleSearch}
            />
          </div>
        );

      case SCREEN_STATES.LOADING:
        return (
          <div id="Text-Input-Section">
            <h1 id="front-panel-title" style={{ opacity: 0 }}>Que empleo buscas?</h1>
            <TextInput
              inputText={inputText}
              setInputText={setInputText}
              setSearchButton={handleSearch}
              textinputContainerWidth={"51.5%"}
              textinputWidth={"10%"}
              hide={true}
            />
          </div>
        );

      case SCREEN_STATES.NO_RESULTS:
        return <Llm_chat SCREEN_STATES={SCREEN_STATES} setOfertas={setOfertas} setScreenState={setScreenState} handleSearch={handleSearch} set_vacio={true} />;

      case SCREEN_STATES.RESULTS:
        return (
          <>
            <div id="Top-Front-Panel-Bar" style={{ marginLeft: IAButton ? "21.5%" : "10%" }}>
              <TextInput
                inputText={inputText}
                setInputText={setInputText}
                setSearchButton={handleSearch}
                textinputContainerWidth={"31.5%"}
                textinputWidth={"70%"}
                margin={"15px"}
              />
              <div id="Type-Attachment-Section" style={{ marginBottom: "10px" }}>
                <div
                  id="Text-Container"
                  style={{ backgroundColor: verPagina === SCREEN_STATES2.OFERTA ? "var(--accent-color)" : "" }}
                  onClick={() => setVerPagina(SCREEN_STATES2.OFERTA)}
                >
                  <span id="Texto-Attachment">Oferta</span>
                </div>
                <div
                  id="Text-Container"
                  style={{ backgroundColor: verPagina === SCREEN_STATES2.PAGINA ? "var(--accent-color)" : "" }}
                  onClick={() => setVerPagina(SCREEN_STATES2.PAGINA)}
                >
                  <span id="Texto-Attachment">Pagina</span>
                </div>
                <div
                  id="Text-Container"
                  style={{ backgroundColor: verPagina === SCREEN_STATES2.MAPA ? "var(--accent-color)" : "" }}
                  onClick={() => setVerPagina(SCREEN_STATES2.MAPA)}
                >
                  <span id="Texto-Attachment">Mapa</span>
                </div>
              </div>
            </div>
            <div id="Job-Search-Section">
              <div id="IA-Section" style={{ width: IAButton ? "22%" : "10%" }}>
                <div
                  id="Hide-IA-Section"
                  onClick={() => setIAButton((prev) => !prev)}
                >
                  <MdArrowBackIosNew
                    size={30}
                    color={mode === "dark" ? "black" : "white"}
                    style={{
                      transform: IAButton ? "rotate(0deg)" : "rotate(180deg)",
                    }}
                  />
                  {!IAButton ? (
                    <div id="Hide-Screen-IA"></div>
                  ) : null}
                </div>
                <div id="IA-Text-Container" style={{ fontFamily: "Roboto" }}>
                  <Markdown>
                    {ofertas.IA_text}
                  </Markdown>
                </div>
              </div>
              <div id="Searching-Message">
                <Map datos={ofertas.Vacantes || datosEjemplo} onClick={(oferta) => setOfertaSeleccionada(oferta)} />
              </div>
              {renderOfertas()}
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return <div id="FrontPanel-Main">{renderContent()}</div>;
}
