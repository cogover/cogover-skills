import com.cogover.callbot.AppConfig;
import com.cogover.callbot.security.SecretResolver;
import com.cogover.callbot.security.VaultKvReader;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.SecureRandom;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.time.Clock;
import java.util.Set;

/**
 * Kiểm tra / tạo signing_secret_key của project Stringee (bảng stringee.dh_account_project).
 *
 * Chạy BÊN TRONG pod stringeex-callbot (dùng cấu hình DB + Vault của pod, mật khẩu không rời pod):
 *   java -cp "/tmp/sk:/app/lib/*" ProjectSigningKey check  PROJECT_ID|WORKSPACE_ID
 *   java -cp "/tmp/sk:/app/lib/*" ProjectSigningKey ensure PROJECT_ID|WORKSPACE_ID
 * WORKSPACE_ID (WS...) được tra ra project qua stringee_x.dh_portal giống admin API của callbot.
 *
 * - Không bao giờ in giá trị key; chỉ in trạng thái và độ dài.
 * - ensure: chỉ ghi khi key NULL/rỗng (không ghi đè), key 32 ký tự chữ+số từ SecureRandom, rồi đọc lại xác nhận.
 * - ensure chỉ được ghi ở namespace thử nghiệm (WRITABLE_NAMESPACES); namespace khác (prod) bị từ chối: prod chỉ đọc.
 */
public class ProjectSigningKey {

    static final Set<String> WRITABLE_NAMESPACES = Set.of("vn-release", "master", "release");
    static final String ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    static final int KEY_LENGTH = 32;

    public static void main(String[] args) throws Exception {
        if (args.length != 2 || !(args[0].equals("check") || args[0].equals("ensure"))) {
            System.out.println("usage: ProjectSigningKey check|ensure PROJECT_ID|WORKSPACE_ID");
            System.exit(2);
        }
        String ns = namespace();
        AppConfig cfg = AppConfig.load(Path.of(System.getProperty("callbot.config", "config/app.conf")), System::getenv);
        SecretResolver secrets = SecretResolver.fromSystem(VaultKvReader.fromEnv(System.getenv(), Clock.systemUTC()).orElse(null));
        try (Connection c = DriverManager.getConnection(cfg.stringeeDbUrl(), cfg.stringeeDbUser(),
                secrets.resolve(cfg.stringeeDbPasswordRef()).orElse(""))) {
            int project = args[1].matches("^[0-9]+$") ? Integer.parseInt(args[1]) : projectOf(c, args[1]);
            Integer before = length(c, project);
            if (before == null) {
                System.out.println("project=" + project + " status=project_not_found namespace=" + ns);
                System.exit(1);
            }
            if (before > 0) {
                System.out.println("project=" + project + " status=existing length=" + before + " namespace=" + ns);
                return;
            }
            if (args[0].equals("check")) {
                System.out.println("project=" + project + " status=missing namespace=" + ns);
                System.exit(3);
            }
            if (!WRITABLE_NAMESPACES.contains(ns)) {
                System.out.println("project=" + project + " status=missing write_refused=prod_read_only namespace=" + ns);
                System.exit(4);
            }
            int updated;
            try (PreparedStatement ps = c.prepareStatement("UPDATE stringee.dh_account_project SET signing_secret_key = ? "
                    + "WHERE id = ? AND (signing_secret_key IS NULL OR signing_secret_key = '')")) {
                ps.setString(1, randomKey());
                ps.setInt(2, project);
                updated = ps.executeUpdate();
            }
            Integer after = length(c, project);
            boolean ok = after != null && after > 0;
            System.out.println("project=" + project + " status=" + (ok ? (updated == 1 ? "created" : "existing") : "update_failed")
                    + " length=" + after + " namespace=" + ns);
            if (!ok) {
                System.exit(5);
            }
        }
    }

    /** Workspace Cogover -> project Stringee (dh_portal; nhiều portal thì lấy portal transfer_from_cogover = 1). */
    static int projectOf(Connection c, String workspaceId) throws Exception {
        if (!workspaceId.matches("^[A-Za-z0-9_-]{1,64}$")) {
            throw new IllegalArgumentException("invalid workspace id");
        }
        java.util.List<int[]> rows = new java.util.ArrayList<>();
        try (PreparedStatement ps = c.prepareStatement(
                "SELECT stringee_project, transfer_from_cogover FROM stringee_x.dh_portal WHERE cogover_workspace_id = ?")) {
            ps.setString(1, workspaceId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    rows.add(new int[]{rs.getInt(1), rs.getInt(2)});
                }
            }
        }
        java.util.List<int[]> picked = rows.size() <= 1 ? rows : rows.stream().filter(r -> r[1] == 1).toList();
        if (picked.size() != 1 || picked.get(0)[0] <= 0) {
            System.out.println("workspace=" + workspaceId + " status=" + (picked.isEmpty() ? "no_portal" : "ambiguous_or_no_project"));
            System.exit(1);
        }
        return picked.get(0)[0];
    }

    /** Độ dài key hiện tại (0 khi NULL/rỗng), null khi không có project. */
    static Integer length(Connection c, int project) throws Exception {
        try (PreparedStatement ps = c.prepareStatement(
                "SELECT COALESCE(CHAR_LENGTH(signing_secret_key), 0) FROM stringee.dh_account_project WHERE id = ?")) {
            ps.setInt(1, project);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getInt(1) : null;
            }
        }
    }

    static String randomKey() {
        SecureRandom rnd = new SecureRandom();
        StringBuilder sb = new StringBuilder(KEY_LENGTH);
        for (int i = 0; i < KEY_LENGTH; i++) {
            sb.append(ALPHABET.charAt(rnd.nextInt(ALPHABET.length())));
        }
        return sb.toString();
    }

    static String namespace() {
        try {
            return Files.readString(Path.of("/var/run/secrets/kubernetes.io/serviceaccount/namespace")).trim();
        } catch (Exception e) {
            return "unknown";
        }
    }
}
