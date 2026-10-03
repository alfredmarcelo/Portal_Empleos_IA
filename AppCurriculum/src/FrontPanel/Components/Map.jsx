
import { MdArrowForward } from "react-icons/md";
import "./Styles/map.css";
import { useState } from "react";

export default function Map({ datos = [], onClick }) {
    const [selectedId, setSelectedId] = useState(null);

    return (
        <div id="Map">
            {datos.map((item, index) => {
                const payload = item?.payload || {};
                const puesto = payload.Puesto || payload.puesto || "Puesto no especificado";
                const modalidad = payload.Modalidad || payload.modalidad || "Presencial";
                const empresa = payload.Nombre_Empresa || payload.nombre_empresa || payload.empresa || payload.Empresa || "Confidencial";
                const sueldo = payload.Sueldo || payload.salario_mostrado || payload.sueldo || "A convenir";
                const ubicacion = payload.Ubicacion || payload.ubicacion || "Santo Domingo";
                const fecha = payload.fecha_publicacion || payload.fecha || payload.Fecha || "Reciente";

                return (
                    <div
                        className={`Map-Item ${selectedId === index ? "selected" : ""}`}
                        key={index}
                        onClick={() => {
                            if (onClick) onClick(item);
                            setSelectedId(index);
                        }}
                        style={selectedId === index ? { backgroundColor: "var(--bg-primary)" } : {}}
                    >
                        <div className="Map-Item-Header">
                            <h3 className="Map-Item-Title" title={puesto}>{puesto}</h3>
                            <span className="Map-Item-Modalidad">{modalidad}</span>
                        </div>
                        <div className="Map-Item-Details">
                            <div className="Map-Item-Detail">
                                <span className="Detail-Value" title={empresa}>{empresa}</span>
                            </div>
                            <div className="Map-Item-Detail">
                                <span className="Detail-Value" title={ubicacion}>{ubicacion}</span>
                            </div>
                            <div className="Map-Item-Detail">
                                <span className="Detail-Value" title={sueldo}>{sueldo}</span>
                            </div>
                            <div className="Map-Item-Detail">
                                <span className="Detail-Value" title={fecha}>{fecha}</span>
                            </div>
                        </div>
                        <div className="Map-Item-Button">
                            <MdArrowForward size={18} />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
