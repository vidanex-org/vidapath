package be.cytomine.config.security;

import be.cytomine.domain.security.TemporaryAccessToken;
import be.cytomine.domain.security.User;
import be.cytomine.service.CurrentUserService;
import be.cytomine.service.security.TemporaryAccessTokenService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Optional;

@Slf4j
public class TemporaryTokenFilter extends OncePerRequestFilter {

    private final TemporaryAccessTokenService temporaryAccessTokenService;
    private final CurrentUserService currentUserService;
    public TemporaryTokenFilter(TemporaryAccessTokenService temporaryAccessTokenService, 
                               CurrentUserService currentUserService) {
        this.temporaryAccessTokenService = temporaryAccessTokenService;
        this.currentUserService = currentUserService;
    }

    @Override
        protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
                throws ServletException, IOException {

            // 首先检查是否已经有认证信息（如JWT认证）
            if (SecurityContextHolder.getContext().getAuthentication() != null) {
                filterChain.doFilter(request, response);
                return;
            }

            // 从请求参数中获取临时访问令牌
            String accessToken = request.getParameter("access_token");
            if (accessToken == null || accessToken.isEmpty()) {
                filterChain.doFilter(request, response);
                return;
            }
            
            log.info("Found access_token parameter: {}", accessToken);

            // 验证临时访问令牌
            try {
                // 尝试从URI中提取项目ID
                Long projectId = extractProjectIdFromUri(request.getRequestURI());
                log.info("Extracted project ID from URI: {}", projectId);

                // 如果能从URI提取到项目ID，则验证令牌是否包含此项目ID
                if (projectId != null) {
                    log.info("Checking token for project ID: {}", projectId);
                    Optional<TemporaryAccessToken> tokenOpt = temporaryAccessTokenService.findByTokenKey(accessToken);
                    
                    if (tokenOpt.isPresent() && temporaryAccessTokenService.isValidToken(accessToken, projectId)) {
                        log.info("Token is valid for project ID: {}", projectId);
                        // 获取真实的User对象
                        User user = currentUserService.getCurrentUser(tokenOpt.get().getUser().getUsername());
                        
                        // 创建认证对象，使用User对象作为principal和details，并获取用户的真实角色权限
                        UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                                user,
                                null,
                                user.getRoles().stream().map(role -> new SimpleGrantedAuthority(role.getAuthority())).toList()
                        );
                        // 设置User对象作为details
                        authentication.setDetails(user);

                        SecurityContextHolder.getContext().setAuthentication(authentication);
                        log.info("Temporary access token validated for project {}", projectId);
                    } else {
                        log.info("Token is invalid or not found for project ID: {}", projectId);
                    }
                } else {
                    log.info("No project ID found in URI, checking token without project binding");
                    // 如果无法从URI提取项目ID，则验证令牌是否存在且有效（不绑定特定项目）
                    Optional<TemporaryAccessToken> tokenOpt = temporaryAccessTokenService.findByTokenKey(accessToken);
                    if (tokenOpt.isPresent() && temporaryAccessTokenService.isValidToken(accessToken)) {
                        log.info("Token is valid without project binding");
                        // 获取真实的User对象
                        User user = currentUserService.getCurrentUser(tokenOpt.get().getUser().getUsername());
                        
                        // 创建认证对象，使用User对象作为principal和details，并获取用户的真实角色权限
                        UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                                user,
                                null,
                                user.getRoles().stream().map(role -> new SimpleGrantedAuthority(role.getAuthority())).toList()
                        );
                        // 设置User对象作为details
                        authentication.setDetails(user);

                        SecurityContextHolder.getContext().setAuthentication(authentication);
                        log.info("Temporary access token validated without project binding");
                    } else {
                        log.info("Token is invalid without project binding");
                    }
                }
            } catch (Exception e) {
                log.warn("Invalid temporary access token: {}", e.getMessage(), e);
            }
            
            log.info("Final authentication context: {}", SecurityContextHolder.getContext().getAuthentication());

            filterChain.doFilter(request, response);
        }


        private Long extractProjectIdFromUri(String uri) {
            // 从URI中提取项目ID，支持多种路径格式：
            // 1. 前端路径: /#/project/103587
            // 2. 后端API路径: /api/project/103587/imageinstance/103600.json
            
            try {
                // 处理前端路径，包括带hash的部分
                if (uri.contains("/#/project/")) {
                    String[] parts = uri.split("/#/project/");
                    if (parts.length > 1) {
                        String projectIdPart = parts[1].split("/")[0];
                        return Long.parseLong(projectIdPart);
                    }
                }
                
                // 处理后端API路径
                if (uri.startsWith("/api/project/")) {
                    String[] parts = uri.substring("/api/project/".length()).split("/");
                    if (parts.length > 0) {
                        return Long.parseLong(parts[0]);
                    }
                }   
            } catch (NumberFormatException e) {
                log.info("Cannot extract project ID from URI: {}", uri);
            }
            return null;
        }
}