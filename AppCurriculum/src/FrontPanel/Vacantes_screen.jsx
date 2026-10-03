import React, { useEffect, useState } from 'react';
import "./Styles/vacantes.css";
import Mapas from "./Components/Mapa";
import { resolverCoordenadasVacante } from './Components/Coordenadas_vacantes';

const TIPOSRUTA = {
    PIE: 'walking',
    AUTO: 'driving',
    MOTOCICLETA: 'cycling'
};

export default function Vacantes_screen({ ofertaSeleccionada }) {
    if (!ofertaSeleccionada) return null;

    const { Puesto, Modalidad, Sueldo, Horario, Ubicacion, Descripcion, Beneficios, Direccion, Requisitos } = ofertaSeleccionada.payload;
    const empresaNombre = ofertaSeleccionada.payload.Nombre_Empresa || ofertaSeleccionada.payload.empresa || ofertaSeleccionada.payload.Empresa || "Confidencial";

    const [ruta, setRuta] = useState([]);
    const [minutos, setMinutos] = useState(0);
    const [distancia, setDistancia] = useState(0);
    const [tiporuta, setTiporuta] = useState(TIPOSRUTA.AUTO);

    // Origen inicial por defecto: Centro de Santo Domingo
    const [position, setPosition] = useState({
        lat: 18.4861,
        lng: -69.9312
    });

    // Destino dinámico resuelto a partir de las coordenadas de la vacante seleccionada
    const [destino, setDestino] = useState(() => resolverCoordenadasVacante(ofertaSeleccionada?.payload));

    // Obtener la ubicación GPS real del usuario si el navegador lo permite
    useEffect(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const lat = pos.coords.latitude;
                    const lng = pos.coords.longitude;
                    if (lat && lng) {
                        setPosition({ lat, lng });
                    }
                },
                (err) => {
                    console.log("Geolocalización por defecto en Santo Domingo:", err.message);
                }
            );
        }
    }, []);

    // Actualizar coordenadas de destino cada vez que cambie la vacante seleccionada
    useEffect(() => {
        if (ofertaSeleccionada?.payload) {
            const nuevasCoords = resolverCoordenadasVacante(ofertaSeleccionada.payload);
            setDestino(nuevasCoords);
        }
    }, [ofertaSeleccionada]);

    // Calcular la ruta OSRM entre el usuario y la vacante
    async function obtenerRutaAPie() {
        try {
            if (!position.lat || !position.lng || !destino.lat || !destino.lng) return [];
            const url =
                `https://router.project-osrm.org/route/v1/${tiporuta}/` +
                `${position.lng},${position.lat};` +
                `${destino.lng},${destino.lat}` +
                '?overview=full&geometries=geojson';

            const res = await fetch(url);
            const data = await res.json();
            if (data?.routes?.[0]) {
                const min = Math.round(data.routes[0].duration / 60);
                const dist = (data.routes[0].distance / 1000).toFixed(1);

                setMinutos(min);
                setDistancia(dist);
                return data.routes[0].geometry.coordinates;
            }
            return [];
        } catch (e) {
            console.warn("No se pudo calcular la ruta:", e);
            return [];
        }
    }

    // Recalcular la ruta cuando cambie el vehículo, la posición de origen o el destino
    useEffect(() => {
        if (destino.lat && destino.lng && position.lat && position.lng) {
            obtenerRutaAPie().then(coords => {
                if (coords && coords.length > 0) {
                    setRuta(coords.map(c => [c[1], c[0]]));
                } else {
                    setRuta([]);
                }
            });
        }
    }, [tiporuta, position, destino]);

    // Normalizar lista de beneficios
    const beneficiosLista = Array.isArray(Beneficios)
        ? Beneficios.filter(b => b && b.trim() !== "").map(b => b.trim().replace(/^[-•✓*]\s*/, ''))
        : (typeof Beneficios === 'string' && Beneficios.trim() !== ""
            ? Beneficios.split(/\r?\n/).filter(b => b && b.trim() !== "").map(b => b.trim().replace(/^[-•✓*]\s*/, ''))
            : []);

    // Normalizar lista de requisitos del puesto
    const requisitosData = Requisitos || ofertaSeleccionada?.payload?.requisitos || ofertaSeleccionada?.payload?.detalles?.requisitos_educativos;
    const requisitosLista = Array.isArray(requisitosData)
        ? requisitosData.filter(r => r && r.trim() !== "").map(r => r.trim().replace(/^[-•✓*]\s*/, ''))
        : (typeof requisitosData === 'string' && requisitosData.trim() !== ""
            ? requisitosData.split(/\r?\n/).filter(r => r && r.trim() !== "").map(r => r.trim().replace(/^[-•✓*]\s*/, ''))
            : [
                "Experiencia previa comprobable en puestos similares o afines al cargo.",
                "Formación académica o técnica requerida para el área.",
                "Capacidad para trabajar en equipo y orientación al logro de objetivos.",
                `Disponibilidad para cumplir con la modalidad ${Modalidad || "Presencial"}.`
            ]);

    return (
        <div className="Vacantes-Container">

            {/* Mitad Superior Simétrica: Mapa (50%) + Información y Grid Simétrico (50%) */}
            <div className="Vacantes-Top">
                <div id="Mapa-Container">
                    <div id="Mapa">
                        <Mapas
                            ruta={ruta}
                            destino={destino}
                            position={position}
                            puesto={Puesto}
                            parametros={true}
                            style={{ height: '100%', borderRadius: '12px' }}
                        />
                    </div>
                </div>

                <div className="Vacantes-Info-Container">
                    <div className="Vacantes-Header">
                        <h2 className="Vacantes-Title">{Puesto}</h2>
                        <span className="Vacantes-Tag">{Modalidad || "No especifica"}</span>
                    </div>

                    <div id="Vacantes-Apply-Container">
                        <button type="button" id="Vacantes-Apply-Button" className="btn-primary">
                            <span>Aplicar</span>
                        </button>
                        <button type="button" id="Vacantes-Apply-Button" className="btn-secondary">
                            <span>Aplicar automatización</span>
                        </button>
                    </div>

                    {/* Grid de Detalles Simétrico: 2 Columnas balanceadas con micro-tarjetas */}
                    <div className="Vacantes-Detail-Grid">
                        <div className="Vacantes-Detail-Cell">
                            <span className="Vacantes-Detail-Label">Sueldo</span>
                            <span className="Vacantes-Detail-Value">{Sueldo || "A convenir"}</span>
                        </div>
                        <div className="Vacantes-Detail-Cell">
                            <span className="Vacantes-Detail-Label">Empresa</span>
                            <span className="Vacantes-Detail-Value">{empresaNombre}</span>
                        </div>

                        <div className="Vacantes-Detail-Cell">
                            <span className="Vacantes-Detail-Label">Ubicación</span>
                            <span className="Vacantes-Detail-Value">{Ubicacion || "Santo Domingo"}</span>
                        </div>
                        <div className="Vacantes-Detail-Cell">
                            <span className="Vacantes-Detail-Label">Distancia Aprox.</span>
                            <span className="Vacantes-Detail-Value">
                                {distancia > 0 ? `${distancia} km (${minutos} min)` : "Calculando..."}
                            </span>
                        </div>
                        <div className="Vacantes-Detail-Cell full-width  ">
                            <span className="Vacantes-Detail-Label">Horario</span>
                            <span className="Vacantes-Detail-Value">{Horario || "Tiempo Completo"}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Mitad Inferior: Descripción a la izquierda y Requisitos + Beneficios a la derecha */}
            <div className="Vacantes-Bottom">
                <div className="Vacantes-Box Vacantes-Description-Box">
                    <h3 className="Vacantes-Section-Title">
                        <span>Descripción del Puesto</span>
                    </h3>
                    <p className="Vacantes-Text">
                        {Descripcion || "No se ha proporcionado una descripción detallada para esta vacante. Consulta directamente con el empleador al postularte."}
                    </p>
                </div>

                <div className="Vacantes-Right-Column">
                    {/* Div justo arriba de beneficios hablando de los requisitos del puesto */}
                    <div className="Vacantes-Box Vacantes-Requirements-Box">
                        <h3 className="Vacantes-Section-Title">
                            <span>Requisitos del Puesto</span>
                        </h3>
                        <ul className="Vacantes-Requirements-List">
                            {requisitosLista.map((r, i) => (
                                <li key={i} className="Vacantes-Requirement-Item">
                                    <span>{r}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="Vacantes-Box Vacantes-Benefits-Box">
                        <h3 className="Vacantes-Section-Title">
                            <span>Beneficios</span>
                        </h3>
                        {beneficiosLista.length > 0 ? (
                            <ul className="Vacantes-Benefits-List">
                                {beneficiosLista.map((b, i) => (
                                    <li key={i} className="Vacantes-Benefit-Item">
                                        <span>{b}</span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <ul className="Vacantes-Benefits-List">
                                <li className="Vacantes-Benefit-Item">
                                    <span>Beneficios de ley (Seguro Familiar de Salud y AFP)</span>
                                </li>
                                <li className="Vacantes-Benefit-Item">
                                    <span>Salario de navidad (Regalía pascual)</span>
                                </li>
                                <li className="Vacantes-Benefit-Item">
                                    <span>Vacaciones laborales remuneradas</span>
                                </li>
                            </ul>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}