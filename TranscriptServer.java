import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class TranscriptServer {
    private static final Path DIR = Path.of(System.getProperty("transcripts", "../transcripts")).toAbsolutePath().normalize();

    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getProperty("port", "8080"));
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/api/transcripts", TranscriptServer::handle);
        server.start();
        System.out.println("Serving " + DIR + " on http://localhost:" + port + "/api/transcripts");
    }

    private static void handle(HttpExchange ex) throws IOException {
        try {
            String path = ex.getRequestURI().getPath();
            String name = path.substring("/api/transcripts".length()).replaceFirst("^/", "");
            if (name.isEmpty()) {
                try (Stream<Path> files = Files.list(DIR)) {
                    List<String> names = files.map(p -> p.getFileName().toString())
                            .filter(n -> n.endsWith(".txt")).sorted().collect(Collectors.toList());
                    String json = names.stream().map(n -> "\"" + escape(n) + "\"")
                            .collect(Collectors.joining(",", "[", "]"));
                    send(ex, 200, "application/json", json);
                }
                return;
            }
            Path file = DIR.resolve(name).normalize();
            if (!file.startsWith(DIR) || !name.endsWith(".txt") || !Files.isRegularFile(file)) {
                send(ex, 404, "text/plain", "not found");
                return;
            }
            send(ex, 200, "text/plain; charset=utf-8", Files.readString(file));
        } catch (Exception e) {
            send(ex, 500, "text/plain", "error");
        }
    }

    private static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static void send(HttpExchange ex, int code, String type, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", type);
        ex.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        ex.sendResponseHeaders(code, bytes.length);
        ex.getResponseBody().write(bytes);
        ex.close();
    }
}
